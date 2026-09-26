import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DOCS_DIR = "./data/documents"
os.makedirs(DOCS_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Heading1'],
    fontSize=18,
    leading=22,
    textColor=colors.HexColor('#1e3a8a'),
    spaceAfter=12
)
heading2_style = ParagraphStyle(
    'DocHeading2',
    parent=styles['Heading2'],
    fontSize=13,
    leading=16,
    textColor=colors.HexColor('#1d4ed8'),
    spaceBefore=10,
    spaceAfter=6
)
body_style = ParagraphStyle(
    'DocBody',
    parent=styles['Normal'],
    fontSize=10,
    leading=14,
    textColor=colors.HexColor('#334155'),
    spaceAfter=8
)
bullet_style = ParagraphStyle(
    'DocBullet',
    parent=styles['Normal'],
    fontSize=10,
    leading=14,
    textColor=colors.HexColor('#334155'),
    leftIndent=15,
    spaceAfter=4
)
meta_style = ParagraphStyle(
    'DocMeta',
    parent=styles['Italic'],
    fontSize=8,
    leading=10,
    textColor=colors.HexColor('#64748b'),
    spaceAfter=14
)

def create_pdf(filename, pages_content):
    filepath = os.path.join(DOCS_DIR, filename)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    story = []
    for i, page in enumerate(pages_content):
        if i > 0:
            story.append(PageBreak())
        for elem in page:
            story.append(elem)
    doc.build(story)
    print(f"Generated: {filepath}")

# 1. Refund Policy.pdf
p1_1 = [
    Paragraph("TechNova Support — Refund Policy", title_style),
    Paragraph("Document ID: POL-REF-2024-V2 | Demo / Fictional Company Policy | Page 1", meta_style),
    Paragraph("Section 1: Overview & Eligibility Window", heading2_style),
    Paragraph("TechNova guarantees high satisfaction across all hardware and software purchases. If you are not fully satisfied, this document outlines return and refund eligibility.", body_style),
    Paragraph("1. Refund Window: All refund requests must be formally submitted within exactly 7 calendar days of carrier delivery confirmation.", bullet_style),
    Paragraph("2. Condition: Returned items must be undamaged, unaltered, and enclosed in original protective packaging with accessories.", bullet_style),
    Paragraph("3. Purchase Verification: Valid proof of purchase (official order invoice or order number) is strictly required.", bullet_style),
    Paragraph("4. Digital Products: Software licenses and digital keys are refundable only if unactivated and unredeemed.", bullet_style),
]
p1_2 = [
    Paragraph("Refund Policy — Processing & Restocking", heading2_style),
    Paragraph("Document ID: POL-REF-2024-V2 | Demo / Fictional Company Policy | Page 2", meta_style),
    Paragraph("Section 2: Inspection and Reimbursement Timelines", heading2_style),
    Paragraph("Upon physical receipt at our inspection warehouse, our Quality Assurance team inspects products within 3 business days.", body_style),
    Paragraph("Reimbursement: Approved refunds are credited to the original payment method within 5 to 7 business days.", bullet_style),
    Paragraph("Domestic Restocking: For change-of-mind returns, a flat $8.50 restocking and shipping fee is deducted. Defective items receive full 100% refund with prepaid shipping.", bullet_style),
    Paragraph("Section 3: International Returns", heading2_style),
    Paragraph("International customers are responsible for all international return postage, customs tariffs, and local brokerage duties. TechNova does not offer prepaid international return labels.", body_style)
]
create_pdf("Refund Policy.pdf", [p1_1, p1_2])

# 2. Shipping Policy.pdf
p2_1 = [
    Paragraph("TechNova Support — Shipping Policy", title_style),
    Paragraph("Document ID: POL-SHP-2024-V3 | Demo / Fictional Company Policy | Page 1", meta_style),
    Paragraph("Section 1: Processing Times & Warehouse Dispatch", heading2_style),
    Paragraph("All orders are fulfilled from our central distribution hubs Monday through Friday between 8:00 AM and 5:00 PM EST.", body_style),
    Paragraph("Standard warehouse processing requires 1 to 2 business days prior to carrier dispatch.", bullet_style),
    Paragraph("Orders received after 2:00 PM EST on Friday are processed on the subsequent Monday morning.", bullet_style),
    Paragraph("Automated email tracking confirmations are sent immediately upon carrier dispatch.", bullet_style),
]
p2_2 = [
    Paragraph("Shipping Policy — Methods & Delivery Timelines", heading2_style),
    Paragraph("Document ID: POL-SHP-2024-V3 | Demo / Fictional Company Policy | Page 2", meta_style),
    Paragraph("Section 2: Delivery Speeds and Freight Charges", heading2_style),
    Paragraph("1. Standard Ground Shipping: Takes 3 to 5 business days for delivery post-dispatch. Complimentary for domestic orders exceeding $50.00; otherwise $5.99 flat fee.", bullet_style),
    Paragraph("2. Expedited Express Delivery: Guaranteed 2 business days delivery post-dispatch for a $14.99 flat fee.", bullet_style),
    Paragraph("3. Priority Overnight Freight: Guaranteed next business day arrival if placed prior to 12:00 PM EST for $29.99.", bullet_style),
    Paragraph("Section 3: International Shipping Destinations", heading2_style),
    Paragraph("TechNova ships internationally to 45 countries. Transit times span 7 to 14 business days subject to local customs clearance.", body_style)
]
create_pdf("Shipping Policy.pdf", [p2_1, p2_2])

# 3. Warranty Policy.pdf
p3_1 = [
    Paragraph("TechNova Support — Hardware Warranty Policy", title_style),
    Paragraph("Document ID: POL-WRT-2024-V2 | Demo / Fictional Company Policy | Page 1", meta_style),
    Paragraph("Section 1: Warranty Coverage Periods", heading2_style),
    Paragraph("Brand-new TechNova hardware devices include a standard 1-year (12-month) limited manufacturer warranty from delivery date.", body_style),
    Paragraph("Refurbished and certified pre-owned units carry an official 90-day limited warranty covering core motherboard, power supply, and display components.", bullet_style),
    Paragraph("Section 2: Scope of Coverage", heading2_style),
    Paragraph("Coverage protects against factory craftsmanship defects and hardware component breakdowns during normal intended operational usage.", body_style),
    Paragraph("Battery degradation: Covered if capacity drops beneath 80% of original factory rated capacity during the first 12 months.", bullet_style),
]
p3_2 = [
    Paragraph("Warranty Policy — Exclusions & Extended Plans", heading2_style),
    Paragraph("Document ID: POL-WRT-2024-V2 | Demo / Fictional Company Policy | Page 2", meta_style),
    Paragraph("Section 3: Explicit Exclusions", heading2_style),
    Paragraph("The standard warranty excludes cosmetic scratches, drops, liquid spills, unauthorized third-party repairs, or unapproved firmware modifications.", body_style),
    Paragraph("Section 4: TechNova Care+ Extended Protection", heading2_style),
    Paragraph("TechNova Care+ extends warranty coverage to 3 full years and includes two incidents of accidental damage handling per year subject to a $49.00 deductible.", body_style)
]
create_pdf("Warranty Policy.pdf", [p3_1, p3_2])

# 4. Cancellation Policy.pdf
p4_1 = [
    Paragraph("TechNova Support — Order Cancellation Policy", title_style),
    Paragraph("Document ID: POL-CAN-2024-V1 | Demo / Fictional Company Policy | Page 1", meta_style),
    Paragraph("Section 1: Immediate Cancellation Window", heading2_style),
    Paragraph("Orders enter automated warehouse picking systems rapidly after credit authorization.", body_style),
    Paragraph("Customers may cancel an order free of charge within 60 minutes of placement directly via their online account dashboard.", bullet_style),
    Paragraph("After 60 minutes, orders are locked in the automated fulfillment queue and cannot be cancelled prior to dispatch.", bullet_style),
    Paragraph("Section 2: In-Transit Orders and Pre-Orders", heading2_style),
    Paragraph("Once handed to the carrier, shipments cannot be intercepted. Customers can decline the shipment at delivery (Return to Sender) or file for a return within 7 days under the Refund Policy.", body_style),
    Paragraph("Pre-ordered items may be cancelled without penalty at any time prior to final dispatch notification.", bullet_style)
]
create_pdf("Cancellation Policy.pdf", [p4_1])

# 5. Return Policy.pdf
p5_1 = [
    Paragraph("TechNova Support — Product Return Policy", title_style),
    Paragraph("Document ID: POL-RET-2024-V1 | Demo / Fictional Company Policy | Page 1", meta_style),
    Paragraph("Section 1: Return Initiation & RMA Process", heading2_style),
    Paragraph("All returns must have an authorized Return Merchandise Authorization (RMA) number generated through our support portal.", body_style),
    Paragraph("Returns must be initiated within 7 calendar days of delivery. Packages returned without an active RMA number will be rejected at the warehouse.", bullet_style),
    Paragraph("Complimentary prepaid domestic labels are provided for defective items or mis-shipped merchandise.", bullet_style),
    Paragraph("Section 2: Packaging Guidelines", heading2_style),
    Paragraph("Customers must securely pack items in original foam inserts and include cables, manuals, and protective shrouds to avoid deduction penalties.", body_style)
]
create_pdf("Return Policy.pdf", [p5_1])

# 6. Customer FAQ.pdf
p6_1 = [
    Paragraph("TechNova Support — General Customer FAQ", title_style),
    Paragraph("Document ID: FAQ-CUS-2024-V2 | Demo / Fictional Company Policy | Page 1", meta_style),
    Paragraph("Section 1: Support Channels and Hours of Operation", heading2_style),
    Paragraph("TechNova provides customer support via three primary modalities:", body_style),
    Paragraph("1. AI Customer Support Assistant: Available 24/7 on our official web portal.", bullet_style),
    Paragraph("2. Live Human Agent Support: Monday through Friday, 8:00 AM to 8:00 PM EST, and Saturday 9:00 AM to 5:00 PM EST.", bullet_style),
    Paragraph("3. Email Support: support@technova-support-demo.com (typical response within 4 business hours).", bullet_style),
    Paragraph("Section 2: Physical Facility & Store Visitation", heading2_style),
    Paragraph("TechNova operates strictly as a direct-to-consumer digital commerce enterprise. Warehouses and distribution hubs are private industrial facilities not open to the general public or pets.", body_style)
]
create_pdf("Customer FAQ.pdf", [p6_1])

# 7. Product Information.pdf
p7_1 = [
    Paragraph("TechNova Support — Product Specifications", title_style),
    Paragraph("Document ID: INF-PRD-2024-V1 | Demo / Fictional Company Policy | Page 1", meta_style),
    Paragraph("Section 1: NovaBook 15 Pro Specifications & RAM Upgrades", heading2_style),
    Paragraph("The NovaBook 15 Pro features dual user-upgradeable DDR5 SO-DIMM memory slots supporting up to 64GB RAM (5600MHz).", body_style),
    Paragraph("Opening the bottom chassis with the included Torx T5 screwdriver does NOT void the manufacturer hardware warranty, provided components are not physically fractured.", bullet_style),
    Paragraph("Section 2: Battery and GaN Charging", heading2_style),
    Paragraph("The 84Wh battery yields up to 14 hours of continuous productivity. A 100W GaN USB-C Power Delivery charger is included in the retail box, achieving 50% charge in 32 minutes.", body_style)
]
create_pdf("Product Information.pdf", [p7_1])

print("All 7 sample policy PDF documents successfully generated.")
