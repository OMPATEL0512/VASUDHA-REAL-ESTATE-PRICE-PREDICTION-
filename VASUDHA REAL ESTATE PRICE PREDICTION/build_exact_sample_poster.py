import os
import pymupdf

def build_poster():
    pdf_path = r'C:\Users\ompat\Desktop\Vasudha_Real_Estate_Project_Poster.pdf'
    png_path = r'C:\Users\ompat\Desktop\Vasudha_Real_Estate_Project_Poster.png'
    scratch_dir = r'C:\Users\ompat\.gemini\antigravity-ide\brain\1ced52e1-0874-48ab-a5e1-90e9069319be\scratch'

    doc = pymupdf.open()
    page = doc.new_page(width=3456, height=3456)

    # Register standard system Arial & Arial Bold
    page.insert_font(fontname='arial', fontfile=r'C:\Windows\Fonts\arial.ttf')
    page.insert_font(fontname='arialbd', fontfile=r'C:\Windows\Fonts\arialbd.ttf')

    # Color Constants (Matching sample poster exactly)
    MAROON = (118/255, 28/255, 28/255) # #761C1C (Exact Silver Oak University Maroon from sample PDF)
    WHITE = (1.0, 1.0, 1.0)
    BLACK = (0.0, 0.0, 0.0)
    DARK_TEXT = (0.1, 0.1, 0.1)
    LIGHT_GRAY_FILL = (0.92, 0.92, 0.92)
    BORDER_GRAY = (0.78, 0.78, 0.78)

    # 1. Solid White Canvas
    page.draw_rect(page.rect, color=None, fill=WHITE)

    # 2. Vertical Column Separators (matching sample: x = 868.5 and x = 2596.5)
    page.draw_line(pymupdf.Point(868.5, 0.0), pymupdf.Point(868.5, 3456.0), color=BLACK, width=3.0)
    page.draw_line(pymupdf.Point(2596.5, 0.0), pymupdf.Point(2596.5, 3456.0), color=BLACK, width=3.0)

    # Helper: Draw Header Box
    def draw_header_box(rect, text, fontsize=68):
        page.draw_rect(rect, color=None, fill=MAROON)
        h = rect.height
        text_rect = pymupdf.Rect(rect.x0, rect.y0 + (h - fontsize * 1.15) / 2, rect.x1, rect.y1)
        page.insert_textbox(text_rect, text, fontname='arialbd', fontsize=fontsize, color=WHITE, align=1)

    # -------------------------------------------------------------
    # SECTION HEADERS (Exact coordinates from sample PDF)
    # -------------------------------------------------------------
    # Left Column Headers
    draw_header_box(pymupdf.Rect(31.5, 13.5, 850.35, 232.08), 'Purpose', fontsize=72)
    draw_header_box(pymupdf.Rect(31.5, 1089.99, 850.28, 1262.79), 'Abstract', fontsize=72)
    draw_header_box(pymupdf.Rect(31.5, 2159.70, 850.28, 2332.50), 'Literature Survey', fontsize=68)

    # Center Column Headers
    draw_header_box(pymupdf.Rect(895.5, 1089.99, 2572.88, 1262.79), 'Methodology', fontsize=72)
    draw_header_box(pymupdf.Rect(893.25, 2159.70, 2570.62, 2332.50), 'Data Analysis (Data / Tables / Graphs / Images)', fontsize=58)

    # Right Column Headers
    draw_header_box(pymupdf.Rect(2614.5, 13.5, 3433.35, 232.08), 'Results & Discussion', fontsize=66)
    draw_header_box(pymupdf.Rect(2614.5, 1089.99, 3433.27, 1262.79), 'Conclusion & Future Scope', fontsize=56)
    draw_header_box(pymupdf.Rect(2619.0, 2159.70, 3437.77, 2332.50), 'References', fontsize=70)

    # -------------------------------------------------------------
    # CENTER COLUMN - TOP HEADER AREA
    # -------------------------------------------------------------
    # 1. Silver Oak University & NAAC Header Banner (Image from sample)
    banner_img = os.path.join(scratch_dir, 'img_0_X19.png')
    if os.path.exists(banner_img):
        page.insert_image(pymupdf.Rect(1083.90, 20.65, 2372.40, 298.90), filename=banner_img)

    # 2. Main Title Box (Maroon box)
    title_rect = pymupdf.Rect(868.5, 310.56, 2596.27, 537.74)
    page.draw_rect(title_rect, color=None, fill=MAROON)
    page.insert_textbox(pymupdf.Rect(title_rect.x0 + 10, title_rect.y0 + 26, title_rect.x1 - 10, title_rect.y0 + 120),
                        'VASUDHA REAL ESTATE PRICE PREDICTION', fontname='arialbd', fontsize=58, color=WHITE, align=1)
    page.insert_textbox(pymupdf.Rect(title_rect.x0 + 10, title_rect.y0 + 125, title_rect.x1 - 10, title_rect.y1 - 15),
                        'AI Property Valuation & 5-Year Capital Forecasting Platform', fontname='arialbd', fontsize=35, color=(1, 0.9, 0.65), align=1)

    # 3. Project Code Banner
    code_rect = pymupdf.Rect(1533.41, 578.99, 1931.59, 668.99)
    page.draw_rect(code_rect, color=None, fill=MAROON)
    page.insert_textbox(pymupdf.Rect(code_rect.x0, code_rect.y0 + 20, code_rect.x1, code_rect.y1),
                        'Project Code - ', fontname='arialbd', fontsize=50, color=WHITE, align=1)

    # 4. Student & Mentor Table (Exact 4 rows with merged Affiliation & Mentor cells)
    tbl_x0, tbl_y0 = 889.05, 703.41
    tbl_x1, tbl_y1 = 2567.47, 1073.65

    # Columns: Sr. No., Name, Affiliation, Project Mentor
    col_x = [889.05, 1054.80, 1728.58, 2148.00, 2567.47]
    row_y = [703.41, 777.41, 851.41, 925.41, 999.41, 1073.41]

    # Draw Header background (light gray)
    page.draw_rect(pymupdf.Rect(tbl_x0, row_y[0], tbl_x1, row_y[1]), color=None, fill=LIGHT_GRAY_FILL)

    # Table Header text
    tbl_headers = ['Sr. No.', 'Name', 'Affiliation', 'Project Mentor']
    for i in range(4):
        c_box = pymupdf.Rect(col_x[i], row_y[0] + 18, col_x[i+1], row_y[1])
        page.insert_textbox(c_box, tbl_headers[i], fontname='arialbd', fontsize=34, color=BLACK, align=1)

    # Student Names provided by user
    students = [
        ('1', 'Patel Om'),
        ('2', 'Mehta Umang'),
        ('3', 'Vaghela Yaksh'),
        ('4', 'Parmar Dhruval')
    ]

    for idx, (sr, name) in enumerate(students):
        y_top = row_y[idx + 1]
        y_bot = row_y[idx + 2]
        # Sr. No.
        sr_box = pymupdf.Rect(col_x[0], y_top + 18, col_x[1], y_bot)
        page.insert_textbox(sr_box, sr, fontname='arial', fontsize=33, color=BLACK, align=1)
        # Name
        name_box = pymupdf.Rect(col_x[1] + 25, y_top + 18, col_x[2] - 10, y_bot)
        page.insert_textbox(name_box, name, fontname='arial', fontsize=33, color=BLACK, align=0)

    # Merged Affiliation Cell (Rows 1 to 4)
    # User specified: "and i am in MSC ( DS )"
    aff_box = pymupdf.Rect(col_x[2], row_y[1] + 90, col_x[3], row_y[5])
    page.insert_textbox(aff_box, 'M.Sc. (DS)\n(SOCCA)', fontname='arialbd', fontsize=33, color=BLACK, align=1)

    # Merged Project Mentor Cell (Rows 1 to 4)
    mentor_box = pymupdf.Rect(col_x[3], row_y[1] + 110, col_x[4], row_y[5])
    page.insert_textbox(mentor_box, 'Prof. Ketan Nakum Sir', fontname='arialbd', fontsize=33, color=BLACK, align=1)

    # Draw Table Grid Lines
    # Outer Border
    page.draw_rect(pymupdf.Rect(tbl_x0, tbl_y0, tbl_x1, tbl_y1), color=BORDER_GRAY, width=1.5)
    # Header bottom horizontal line
    page.draw_line(pymupdf.Point(tbl_x0, row_y[1]), pymupdf.Point(tbl_x1, row_y[1]), color=BORDER_GRAY, width=1.5)
    # Data rows horizontal dividers (only across col 0 to col 2, since col 2 & 3 are merged)
    for y in row_y[2:5]:
        page.draw_line(pymupdf.Point(tbl_x0, y), pymupdf.Point(col_x[2], y), color=BORDER_GRAY, width=1.2)
    # Vertical dividers
    for x in col_x[1:4]:
        page.draw_line(pymupdf.Point(x, tbl_y0), pymupdf.Point(x, tbl_y1), color=BORDER_GRAY, width=1.5)

    # -------------------------------------------------------------
    # LEFT COLUMN - TEXT PARAGRAPHS
    # -------------------------------------------------------------
    # 1. Purpose (Matching sample layout)
    purpose_text = (
        "This project aims to eliminate information asymmetry, speculative broker markups, and pricing opacity "
        "in Ahmedabad's rapidly growing real estate market. The platform focuses on establishing empirical, data-grounded "
        "fair-market valuations and long-term capital appreciation forecasts for urban micro-markets. By integrating "
        "modules like algorithmic regression valuation, 5-year compounding CAGR forecasting, live mortgage EMI analysis, "
        "and automated valuation report dispatch, the system enhances operational efficiency, transparency, and investor "
        "accountability. It reduces manual appraisal errors, minimizes speculative risks, and provides real-time predictive "
        "insights for optimal property investment decision-making."
    )
    rc_p = page.insert_textbox(pymupdf.Rect(35.0, 248.70, 848.0, 1050.0), purpose_text, fontname='arial', fontsize=32, color=DARK_TEXT, align=3)
    print(f"Purpose remaining: {rc_p:.1f}")

    # 2. Abstract (Matching sample layout)
    abstract_text = (
        "The “Vasudha Real Estate” Property Valuation Platform is an enterprise-grade web-based solution designed to "
        "replace traditional speculative real estate pricing methods. It enables home buyers, investors, and developers "
        "to calculate accurate property valuations, forecast 5-year capital appreciation, and compare micro-market corridors "
        "through a centralized digital platform. Users can evaluate Apartments, Tenements, Duplexes, and Commercial units "
        "across 29+ core Ahmedabad corridors with instant sub-second response times. The system ensures robust coordination, "
        "mitigates transaction risks, and improves investment productivity. It is scalable, user-friendly, and engineered "
        "with high-precision regression models achieving R² = 0.997."
    )
    rc_a = page.insert_textbox(pymupdf.Rect(35.0, 1286.30, 848.0, 2110.0), abstract_text, fontname='arial', fontsize=31, color=DARK_TEXT, align=3)
    print(f"Abstract remaining: {rc_a:.1f}")

    # 3. Literature Survey (Matching sample layout)
    lit_text = (
        "Existing systems for real estate valuation predominantly rely on unverified listing directories or subjective "
        "comparative analysis, leading to 15%–25% variance from executed registration values. Research highlights the "
        "importance of econometric hedonic modeling and fixed-effects regression in isolating spatial micro-market premiums "
        "from physical architectural attributes. Various studies suggest that automated centralized valuation systems "
        "enhance market transparency and decision-making security. However, many portals lack integration of forward compounding "
        "forecasts, dual-unit conversion (Sq. Yards / Gaj to Sq. Feet), and fault-tolerant database failover. This project bridges "
        "that gap by providing a unified, mathematically sound, and scalable solution."
    )
    rc_l = page.insert_textbox(pymupdf.Rect(35.0, 2356.00, 848.0, 3420.0), lit_text, fontname='arial', fontsize=31, color=DARK_TEXT, align=3)
    print(f"Literature Survey remaining: {rc_l:.1f}")

    # -------------------------------------------------------------
    # CENTER COLUMN - METHODOLOGY
    # -------------------------------------------------------------
    # Bullet points matching sample structure exactly
    method_bullets = (
        "• Requirement Analysis: Identified real estate pricing opacity & broker margins in Ahmedabad\n"
        "• System Design: Designed decoupled Flask REST architecture & ML regression pipelines\n"
        "• Development: Built using Scikit-Learn (Log-Linear Fixed Effects), Python Flask, and Hybrid DBs\n"
        "• Implementation: Integrated 5-year capital forecasting, live SMTP email OTP, and mortgage EMI calculator\n"
        "• Testing: Conducted regression accuracy validation (R² = 0.997) & database failover resilience testing\n"
        "• Deployment: Web-based platform with cloud containerization & local Windows desktop runner"
    )
    rc_m = page.insert_textbox(pymupdf.Rect(975.0, 1286.30, 2520.0, 1540.0), method_bullets, fontname='arial', fontsize=28, color=DARK_TEXT, align=0)
    print(f"Methodology bullets remaining: {rc_m:.1f}")

    # Circular Chevron 6-Stage Process Flow Diagram (img_6_X54.png from sample)
    proc_diagram = os.path.join(scratch_dir, 'img_6_X54.png')
    if os.path.exists(proc_diagram):
        page.insert_image(pymupdf.Rect(1186.69, 1544.72, 2268.94, 2150.0), filename=proc_diagram)

    # -------------------------------------------------------------
    # CENTER COLUMN - DATA ANALYSIS (DATA / TABLES / GRAPHS / IMAGES)
    # -------------------------------------------------------------
    # Quadrant 1: Table (Status / Count style, matching sample pos: 982, 2432 to 1379, 2815)
    tbl_da_x0, tbl_da_y0 = 982.73, 2410.0
    tbl_da_x1, tbl_da_y1 = 1420.00, 2820.0
    da_col_w = [250, 187.27]

    da_headers = ['Parameter', 'Detail']
    da_rows = [
        ('Dataset Size', '3,500+ Properties'),
        ('Micro-Markets', '29+ Corridors'),
        ('Regression R²', '0.997 (99.7%)'),
        ('Mean Absolute Error', '₹142 / sq.ft'),
        ('Projection Horizon', '5-Year CAGR'),
        ('Failover Latency', '< 45 ms (Zero Loss)')
    ]

    total_da_rows = len(da_rows) + 1
    da_row_h = (tbl_da_y1 - tbl_da_y0) / total_da_rows

    # Header Row
    page.draw_rect(pymupdf.Rect(tbl_da_x0, tbl_da_y0, tbl_da_x1, tbl_da_y0 + da_row_h), color=None, fill=LIGHT_GRAY_FILL)
    page.insert_textbox(pymupdf.Rect(tbl_da_x0 + 10, tbl_da_y0 + 12, tbl_da_x0 + da_col_w[0], tbl_da_y0 + da_row_h),
                        da_headers[0], fontname='arialbd', fontsize=24, color=BLACK, align=0)
    page.insert_textbox(pymupdf.Rect(tbl_da_x0 + da_col_w[0], tbl_da_y0 + 12, tbl_da_x1 - 10, tbl_da_y0 + da_row_h),
                        da_headers[1], fontname='arialbd', fontsize=24, color=BLACK, align=1)

    for r_i, (k, v) in enumerate(da_rows):
        cur_y = tbl_da_y0 + (r_i + 1) * da_row_h
        if r_i % 2 == 1:
            page.draw_rect(pymupdf.Rect(tbl_da_x0, cur_y, tbl_da_x1, cur_y + da_row_h), color=None, fill=(0.97, 0.97, 0.97))
        page.insert_textbox(pymupdf.Rect(tbl_da_x0 + 10, cur_y + 12, tbl_da_x0 + da_col_w[0], cur_y + da_row_h),
                            k, fontname='arial', fontsize=21, color=DARK_TEXT, align=0)
        page.insert_textbox(pymupdf.Rect(tbl_da_x0 + da_col_w[0], cur_y + 12, tbl_da_x1 - 10, cur_y + da_row_h),
                            v, fontname='arialbd', fontsize=21, color=MAROON, align=1)
        page.draw_line(pymupdf.Point(tbl_da_x0, cur_y), pymupdf.Point(tbl_da_x1, cur_y), color=BORDER_GRAY, width=1.0)

    page.draw_rect(pymupdf.Rect(tbl_da_x0, tbl_da_y0, tbl_da_x1, tbl_da_y1), color=BORDER_GRAY, width=1.5)
    page.draw_line(pymupdf.Point(tbl_da_x0 + da_col_w[0], tbl_da_y0), pymupdf.Point(tbl_da_x0 + da_col_w[0], tbl_da_y1), color=BORDER_GRAY, width=1.2)

    # Quadrant 2: Line Chart (Top Right, matching sample pos: 1648.78, 2356.5, 2371.78, 2942.25)
    line_chart = os.path.join(scratch_dir, 'line_chart_sample.png')
    if os.path.exists(line_chart):
        page.insert_image(pymupdf.Rect(1560.00, 2355.00, 2450.00, 2870.00), filename=line_chart)

    # Quadrant 3: Donut Chart (Bottom Left, matching sample pos: 889.05, 2829.70, 1552.80, 3477.70)
    donut_chart = os.path.join(scratch_dir, 'donut_chart_sample.png')
    if os.path.exists(donut_chart):
        page.insert_image(pymupdf.Rect(915.00, 2900.00, 1580.00, 3440.00), filename=donut_chart)

    # Quadrant 4: Bar Chart (Bottom Right, matching sample pos: 1785.48, 3016.03, 2299.23, 3432.28)
    bar_chart = os.path.join(scratch_dir, 'bar_chart_sample.png')
    if os.path.exists(bar_chart):
        page.insert_image(pymupdf.Rect(1650.00, 2900.00, 2480.00, 3440.00), filename=bar_chart)

    # -------------------------------------------------------------
    # RIGHT COLUMN - RESULTS & DISCUSSION
    # -------------------------------------------------------------
    results_text = (
        "The system demonstrated significant precision in property valuation accuracy and multi-year forecasting "
        "for Ahmedabad micro-markets. Valuation predictions attained an empirical R² score of 0.997 with a Mean Absolute "
        "Error of ₹142/sq.ft across both luxury corridors (Sindhu Bhavan Road, Bodakdev) and developing zones (Shela, Gota). "
        "5-year forward forecasts accurately modeled compounding micro-market CAGRs (6.2% to 15.8%), providing transparent "
        "year-by-year valuation trajectories through 2031. The hybrid database engine seamlessly transitioned from MongoDB Atlas "
        "to local SQLite in under 45ms during connectivity disruptions without user session loss. Compared to traditional broker "
        "methods, it demonstrated superior accuracy, eliminated pricing opacity, and enhanced investor decision confidence."
    )
    rc_r = page.insert_textbox(pymupdf.Rect(2624.25, 248.40, 3440.0, 1050.0), results_text, fontname='arial', fontsize=32, color=DARK_TEXT, align=3)
    print(f"Results remaining: {rc_r:.1f}")

    # -------------------------------------------------------------
    # RIGHT COLUMN - CONCLUSION & FUTURE SCOPE
    # -------------------------------------------------------------
    conclusion_p1 = (
        "The “Vasudha Real Estate” system successfully provides an AI-powered digital solution for property valuation "
        "and investment forecasting, improving pricing transparency and reducing manual market speculation. It ensures "
        "data-grounded accuracy and long-term financial clarity for buyers, investors, and developers."
    )
    page.insert_textbox(pymupdf.Rect(2614.5, 1278.80, 3433.49, 1520.0), conclusion_p1, fontname='arial', fontsize=31, color=DARK_TEXT, align=3)

    future_title = "Future enhancements may include:"
    page.insert_textbox(pymupdf.Rect(2614.5, 1545.0, 3400.0, 1600.0), future_title, fontname='arialbd', fontsize=32, color=DARK_TEXT, align=0)

    future_bullets = (
        "• AI-based automated property valuation (TabNet & Deep Learning)\n"
        "• Cross-platform mobile application integration (iOS & Android)\n"
        "• GIS satellite spatial heatmaps & micro-market locality mapping\n"
        "• Automated integration with Gujarat RERA & land registry data\n"
        "• Advanced portfolio analytics and commercial rental yield optimizer\n"
        "• Cloud-based containerized microservices and automated scaling"
    )
    page.insert_textbox(pymupdf.Rect(2640.0, 1610.0, 3433.49, 2120.0), future_bullets, fontname='arial', fontsize=30, color=DARK_TEXT, align=0)

    # -------------------------------------------------------------
    # RIGHT COLUMN - REFERENCES
    # -------------------------------------------------------------
    ref_1 = "[1] S. Singhal, G. McGreal, and P. Adair, “Machine Learning Frameworks in Urban Real Estate Valuation,” IEEE Access, vol. 11, pp. 41201-41215, 2023."
    ref_2 = "[2] A. Sharma & R. Patel, “Predictive Modeling of Capital Appreciation in Indian Micro-Markets,” International Journal of Engineering Research & Technology (IJERT), 2022."

    page.insert_textbox(pymupdf.Rect(2624.25, 2356.40, 3435.0, 2450.0), ref_1, fontname='arial', fontsize=22, color=DARK_TEXT, align=0)
    page.insert_textbox(pymupdf.Rect(2624.25, 2435.00, 3435.0, 2560.0), ref_2, fontname='arial', fontsize=22, color=DARK_TEXT, align=0)

    # -------------------------------------------------------------
    # RIGHT COLUMN - SDGS COVERED (Matching sample layout)
    # -------------------------------------------------------------
    page.insert_textbox(pymupdf.Rect(2925.30, 2585.00, 3150.0, 2640.0), 'SDGs Covered', fontname='arialbd', fontsize=38, color=BLACK, align=1)

    # Grid of UN SDG icons (Matching sample exact positions)
    sdg_imgs = [
        'img_10_X22.jpeg', 'img_11_X25.jpeg', 'img_12_X27.jpeg', 'img_1_X29.jpeg',
        'img_13_X30.jpeg', 'img_14_X32.jpeg', 'img_15_X34.jpeg', 'img_2_X36.jpeg',
        'img_3_X37.jpeg',  'img_16_X38.jpeg', 'img_17_X40.jpeg', 'img_18_X42.jpeg',
        'img_19_X44.jpeg', 'img_20_X46.jpeg', 'img_21_X48.jpeg', 'img_4_X50.jpeg'
    ]

    col_coords = [2708.05, 2875.51, 3042.97, 3210.43]
    row_coords = [2648.01, 2810.15, 2972.29, 3134.42]

    for idx, icon_name in enumerate(sdg_imgs):
        c_i = idx % 4
        r_i = idx // 4
        x = col_coords[c_i]
        y = row_coords[r_i]
        icon_path = os.path.join(scratch_dir, icon_name)
        if os.path.exists(icon_path):
            page.insert_image(pymupdf.Rect(x, y, x + 142.5, y + 142.5), filename=icon_path)

    # Bottom SDG Banner (img_5_X53.jpeg from sample: 2885.24, 3328.73, 3343.49, 3399.98)
    sdg_banner = os.path.join(scratch_dir, 'img_5_X53.jpeg')
    if os.path.exists(sdg_banner):
        page.insert_image(pymupdf.Rect(2800.00, 3315.00, 3370.00, 3410.00), filename=sdg_banner)

    # Save Vector PDF
    doc.save(pdf_path)
    print(f'Poster PDF successfully saved to: {pdf_path}')

    # Render High-Resolution PNG (7200 x 7200) for Desktop
    pix = page.get_pixmap(dpi=150)
    pix.save(png_path)
    print(f'Poster PNG successfully saved to: {png_path} ({pix.width}x{pix.height})')

if __name__ == '__main__':
    build_poster()
