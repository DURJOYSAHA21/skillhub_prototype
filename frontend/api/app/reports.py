"""PDF generation: payment receipt + completion certificate (fpdf2)."""
from datetime import datetime
from fpdf import FPDF


def _base(title, subtitle):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(16, 185, 129)
    pdf.rect(0, 0, 210, 8, "F")
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(0, 16, "Skillhub", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 8, subtitle, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(30, 41, 59)
    pdf.ln(6)
    return pdf


def receipt_pdf(txn, course_title, learner_name, mentor_name) -> bytes:
    pdf = _base("Payment Receipt", "One Platform to Learn Every Skill")
    for label, val in [("Receipt No", txn.ref), ("Date", txn.created.strftime("%Y-%m-%d %H:%M")),
                       ("Learner", learner_name), ("Course", course_title),
                       ("Mentor", mentor_name), ("Method", txn.method),
                       ("Card", "**** **** **** " + (txn.card_last4 or "----")),
                       ("Status", txn.status.title()),
                       ("Amount", f"BDT {txn.amount:,.2f}")]:
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(55, 9, label + ":")
        pdf.set_font("helvetica", "", 11)
        pdf.cell(0, 9, str(val), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("helvetica", "I", 9)
    pdf.multi_cell(0, 5, "This is a system-generated receipt from the Skillhub "
                        f"simulated payment gateway. Issued {datetime.utcnow():%Y-%m-%d}.")
    return bytes(pdf.output())


def certificate_pdf(learner_name, course_title, hours, done_date) -> bytes:
    pdf = _base("Certificate of Completion", "")
    pdf.ln(4)
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, "This is to certify that", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 12, learner_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, "has successfully completed the course", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 15)
    pdf.cell(0, 11, course_title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"({hours:g} hours) on {done_date:%B %d, %Y}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("helvetica", "I", 9)
    pdf.cell(0, 8, "Skillhub - One Platform to Learn Every Skill | Verify at skillhub.dev/verify")
    return bytes(pdf.output())
