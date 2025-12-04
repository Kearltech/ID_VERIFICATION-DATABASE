from PIL import Image, ImageDraw, ImageFont

# Create a synthetic sample ID card image for demo purposes
W, H = 1200, 800
bg = (245, 245, 250)
card = Image.new('RGB', (W, H), bg)
d = ImageDraw.Draw(card)

# Draw a header box
header_h = 140
d.rectangle([(0,0),(W,header_h)], fill=(10,80,160))

# Add title text
try:
    font_title = ImageFont.truetype('arial.ttf', 48)
    font_label = ImageFont.truetype('arial.ttf', 28)
    font_val = ImageFont.truetype('arial.ttf', 32)
except Exception:
    from PIL import ImageFont
    font_title = ImageFont.load_default()
    font_label = ImageFont.load_default()
    font_val = ImageFont.load_default()

d.text((30, 30), 'REPUBLIC OF GHANA', fill=(255,255,255), font=font_title)
d.text((30, 90), 'National Identity Card (Sample)', fill=(255,255,255), font=font_label)

# Add mock photo box
photo_box = (50, 180, 350, 580)
d.rectangle(photo_box, outline=(0,0,0), width=3, fill=(220,220,220))
d.text((photo_box[0]+20, photo_box[1]+10), 'PHOTO', fill=(80,80,80), font=font_label)

# Add fields labels and values
labels = [
    ('Name', 'KWAME NKRUMAH'),
    ('Date of Birth', '1990-05-15'),
    ('ID Number', 'GHA-123456789-0'),
    ('Sex', 'M'),
    ('Nationality', 'GHANAIAN')
]

x0 = 400
y0 = 200
spacing = 70
for i, (lab, val) in enumerate(labels):
    y = y0 + i*spacing
    d.text((x0, y), f"{lab}:", fill=(20,20,20), font=font_label)
    d.text((x0+220, y), val, fill=(10,10,10), font=font_val)

# Add card footer
d.text((30, H-60), 'Sample Card — For Demo Only', fill=(120,120,120), font=font_label)

# Save
out_path = 'sample_card.jpg'
card.save(out_path, quality=90)
print(f'Created sample card image: {out_path}')

