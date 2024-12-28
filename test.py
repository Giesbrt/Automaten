from PySide6.QtGui import QColor

# Create a QColor in RGB format
color = QColor(255, 100, 50)

# Convert to another color space, for example, HSV
hsv_color = color.convertTo(QColor.Spec.Cmyk)

print("Original color (RGB):", color.name())
print("Converted color (HSV):", hsv_color.name(QColor.NameFormat.HexArgb))
