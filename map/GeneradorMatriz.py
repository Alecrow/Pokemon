#!/usr/bin/env python3
import argparse
import os
import cv2
import numpy as np
import pandas as pd

def load_image(path):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"No pude leer la imagen: {path}")
    # Si trae alfa, compón sobre blanco para colores consistentes
    if img.shape[2] == 4:
        b,g,r,a = cv2.split(img)
        alpha = a.astype(float)/255.0
        bg = np.ones_like(b, dtype=float)*255.0
        b = (b*alpha + bg*(1-alpha)).astype(np.uint8)
        g = (g*alpha + bg*(1-alpha)).astype(np.uint8)
        r = (r*alpha + bg*(1-alpha)).astype(np.uint8)
        img = cv2.merge([b,g,r])
    return img

def tile_iter(h, w, tile):
    nrows = h // tile
    ncols = w // tile
    for r in range(nrows):
        for c in range(ncols):
            y0, y1 = r*tile, (r+1)*tile
            x0, x1 = c*tile, (c+1)*tile
            yield r, c, y0, y1, x0, x1

def hsv_mask(img_bgr, hue_ranges, s_min=60, v_min=60):
    """Devuelve máscara bool para un conjunto de rangos de tono (en OpenCV H=0..179)."""
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]
    mask = np.zeros(H.shape, dtype=bool)
    for lo, hi in hue_ranges:
        if lo <= hi:
            m = (H >= lo) & (H <= hi)
        else:
            # rango que cruza 0
            m = (H >= lo) | (H <= hi)
        mask |= m
    mask &= (S >= s_min) & (V >= v_min)
    return mask

def majority(mask, y0, y1, x0, x1):
    """True si la mayoría del bloque es True (robusto)."""
    blk = mask[y0:y1, x0:x1]
    if blk.size == 0:
        return False
    return (blk.mean() > 0.5)

def main():
    ap = argparse.ArgumentParser(description="Construye matriz de baldosas desde máscaras (transitable/obstáculo/encuentro).")
    ap.add_argument("--mask", help="PNG único con colores (verde=transitable, rojo=obstáculo).")
    ap.add_argument("--passable", help="PNG con transitables (si usas 2 imágenes).")
    ap.add_argument("--blocked", help="PNG con obstáculos (si usas 2 imágenes).")
    ap.add_argument("--encounter", help="PNG con zonas de aparición (opcional).")
    ap.add_argument("--tile", type=int, default=16, help="Tamaño de baldosa en píxeles (default: 16).")
    ap.add_argument("--out_csv", default="grid_labels.csv", help="Salida CSV.")
    ap.add_argument("--out_overlay", default="grid_overlay.png", help="PNG de validación.")
    ap.add_argument("--debug", action="store_true", help="Muestra info adicional.")
    args = ap.parse_args()

    if not args.mask and not (args.passable and args.blocked):
        ap.error("Debes pasar --mask o bien --passable y --blocked.")

    # 1) Cargar imágenes base
    if args.mask:
        img = load_image(args.mask)
        h, w, _ = img.shape
        # Heurísticas HSV:
        # verde ≈ 40..90, rojo ≈ [0..10] ∪ [170..179]
        green_mask = hsv_mask(img, hue_ranges=[(40, 90)], s_min=60, v_min=60)
        red_mask   = hsv_mask(img, hue_ranges=[(0, 10), (170, 179)], s_min=60, v_min=60)
        # Default: si no cae en verde o rojo, lo tratamos como "otro" (no transitable).
        has_encounter_img = False
        enc_mask_full = None
    else:
        # Dos imágenes: transitables/obstáculos
        img_pass = load_image(args.passable)
        img_block = load_image(args.blocked)
        if img_pass.shape != img_block.shape:
            raise ValueError("Las imágenes passable y blocked no tienen el mismo tamaño.")
        h, w, _ = img_pass.shape
        # Derivar máscaras binarias por umbral (no-blanco/negro):
        def nonwhite_mask(im):
            # cualquier cosa que no sea casi blanco la consideramos "marcada"
            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            return (gray < 240)
        green_mask = nonwhite_mask(img_pass)   # transitable
        red_mask   = nonwhite_mask(img_block)  # bloqueado
        has_encounter_img = False
        enc_mask_full = None

    # Zonas de aparición (encuentro) opcional
    if args.encounter:
        enc_img = load_image(args.encounter)
        if enc_img.shape[:2] != (h, w):
            raise ValueError("La imagen de encounter no coincide en tamaño con la base.")
        # Detectar “pasto”: por defecto usamos verde otra vez; ajusta si tu máscara es distinta:
        enc_mask_full = hsv_mask(enc_img, hue_ranges=[(40, 90)], s_min=40, v_min=40)
        has_encounter_img = True

    tile = args.tile
    nrows = h // tile
    ncols = w // tile

    # 2) Construir matriz por celdas
    rows_out = []
    for r, c, y0, y1, x0, x1 in tile_iter(h, w, tile):
        # Si alguna imagen no calza exacto, recortamos a múltiplos de tile
        y1 = min(y1, h); x1 = min(x1, w)
        is_green = majority(green_mask, y0, y1, x0, x1)
        is_red   = majority(red_mask,   y0, y1, x0, x1)
        # Resolución de conflictos: rojo gana a verde (bloqueado tiene prioridad)
        passable = 1 if (is_green and not is_red) else 0
        if has_encounter_img and enc_mask_full is not None:
            enc = 1 if majority(enc_mask_full, y0, y1, x0, x1) else 0
        else:
            # Si no hay máscara de encounter, puedes inferir encounter del “verde” de tu máscara
            # sólo si el verde en esa export corresponde a pasto. Si tu export marca camino como verde,
            # deja encounter=0 y luego podrás suministrar una máscara específica.
            enc = 0
        rows_out.append({
            "row": r, "col": c,
            "passable": passable,
            "encounter": enc
        })

    df = pd.DataFrame(rows_out)
    df.to_csv(args.out_csv, index=False)

    # 3) Overlay de validación
    # Pintamos celdas transitables en cian, bloqueadas en rojo; encounter agrega verde encima.
    overlay = np.ones((h, w, 3), dtype=np.uint8)*255
    for r, c, y0, y1, x0, x1 in tile_iter(h, w, tile):
        rec = df[(df.row==r) & (df.col==c)].iloc[0]
        if rec.passable == 1:
            color = (255, 200, 0)  # BGR cian-ish (para OpenCV: (B,G,R) → (255,200,0))
        else:
            color = (0, 0, 255)    # rojo
        cv2.rectangle(overlay, (x0, y0), (x1-1, y1-1), color, thickness=-1)
        if rec.encounter == 1:
            # mezclar verde encima
            sub = overlay[y0:y1, x0:x1].astype(np.float32)
            sub = sub*0.5 + np.array([0,255,0], dtype=np.float32)*0.5
            overlay[y0:y1, x0:x1] = sub.astype(np.uint8)

    # Rejilla para referencia
    for r in range(nrows+1):
        y = min(r*tile, h-1)
        cv2.line(overlay, (0,y), (w-1,y), (0,0,0), 1)
    for c in range(ncols+1):
        x = min(c*tile, w-1)
        cv2.line(overlay, (x,0), (x,h-1), (0,0,0), 1)

    cv2.imwrite(args.out_overlay, overlay)
    if args.debug:
        print(f"Guardado CSV: {args.out_csv}")
        print(f"Guardado overlay: {args.out_overlay}")
        print(f"Dimensión grilla: {nrows}x{ncols} celdas")

if __name__ == "__main__":
    main()
