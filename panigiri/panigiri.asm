; panigiri.asm — ολόκληρη οθόνη Mode 2 για Amstrad CPC 6128
; ΠΑΡΑΓΕΤΑΙ ΑΥΤΟΜΑΤΑ από src/make_screen.py — μην το πειράζεις.
;
; Δείχνει την εικόνα και περιμένει πλήκτρο. Τα δεδομένα είναι ήδη στη
; διάταξη της μνήμης οθόνης, οπότε η εμφάνιση είναι ένα LDIR.

SCR_SET_MODE  equ #BC0E
SCR_SET_INK   equ #BC32
SCR_SET_BORDER equ #BC38
KM_WAIT_CHAR  equ #BB06

    org #4000
    run start

start:
    ld a,2
    call SCR_SET_MODE          ; Mode 2, 640x200, 2 pens

    ld hl,inks
    ld e,0                     ; e = αριθμός pen
ink_loop:
    ld a,(hl)
    ld b,a
    ld c,a                     ; b=c -> σταθερό χρώμα, χωρίς flashing
    ld a,e
    push hl
    push de
    call SCR_SET_INK
    pop de
    pop hl
    inc hl
    inc e
    ld a,e
    cp 2
    jr nz,ink_loop

    ld a,(inks)                ; το border στο ίδιο με το pen 0
    ld b,a
    ld c,a
    call SCR_SET_BORDER

    ld hl,picture              ; η οθόνη, έτοιμη
    ld de,#C000
    ld bc,#4000
    ldir

    call KM_WAIT_CHAR          ; μένει ώσπου να πατήσεις πλήκτρο
    jp #0000                   ; και μετά reset

inks:
    db 0,26   ; firmware numbers, pen 0..1

picture:
    incbin "panigiri.scr"
