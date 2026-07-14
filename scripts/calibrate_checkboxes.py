"""Find checkbox Y positions on page 1."""
import fitz

with open("tmp_cb.txt", "w", encoding="utf-8") as f:
    for pdf in ["Form/adult_vn.pdf", "Form/Child_vn.pdf"]:
        page = fitz.open(pdf)[0]
        f.write(pdf + "\n")
        for w in sorted(page.get_text("words"), key=lambda w: (w[1], w[0])):
            t = w[4]
            if any(k in t for k in ("Medi-Cal", "PPO", "HMO", "Châu", "Nam", "thuốc", "Bảo")):
                f.write(f"  y={w[1]:.0f} x={w[0]:.0f} {t}\n")
