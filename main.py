# Image Edit App - PyQt5 + PIL
# Features: open/save, crop, resize, rotate, brightness/contrast, filters, undo/redo
# Author: Rahit Biswas (rahit91890)

import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PIL import Image, ImageFilter, ImageEnhance, ImageQt
import io

class HistoryStack:
    def __init__(self, limit=20):
        self.stack = []
        self.index = -1
        self.limit = limit
    def push(self, img):
        # truncate forward
        if self.index < len(self.stack) - 1:
            self.stack = self.stack[: self.index + 1]
        # clone image to avoid shared state
        self.stack.append(img.copy())
        # trim
        if len(self.stack) > self.limit:
            self.stack.pop(0)
        self.index = len(self.stack) - 1
    def can_undo(self):
        return self.index > 0
    def can_redo(self):
        return self.index < len(self.stack) - 1
    def undo(self):
        if self.can_undo():
            self.index -= 1
            return self.stack[self.index].copy()
        return None
    def redo(self):
        if self.can_redo():
            self.index += 1
            return self.stack[self.index].copy()
        return None
    def current(self):
        if 0 <= self.index < len(self.stack):
            return self.stack[self.index].copy()
        return None

class ImageEditor(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Edit App - PyQt5")
        self.resize(1100, 700)
        self.image = None  # PIL Image
        self.path = None
        self.history = HistoryStack()
        self.crop_mode = False
        self.crop_start = None
        self.crop_end = None

        self._build_ui()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)

        # Left: Tools
        tool_panel = QtWidgets.QVBoxLayout()
        open_btn = QtWidgets.QPushButton("Open")
        save_btn = QtWidgets.QPushButton("Save As")
        undo_btn = QtWidgets.QPushButton("Undo")
        redo_btn = QtWidgets.QPushButton("Redo")
        rotate_left_btn = QtWidgets.QPushButton("Rotate -90°")
        rotate_right_btn = QtWidgets.QPushButton("Rotate +90°")
        resize_btn = QtWidgets.QPushButton("Resize…")
        crop_btn = QtWidgets.QPushButton("Crop (drag)")
        grayscale_btn = QtWidgets.QPushButton("Grayscale")
        blur_btn = QtWidgets.QPushButton("Blur")
        sharpen_btn = QtWidgets.QPushButton("Sharpen")

        tool_panel_widgets = [
            open_btn, save_btn, undo_btn, redo_btn, rotate_left_btn, rotate_right_btn,
            resize_btn, crop_btn, grayscale_btn, blur_btn, sharpen_btn
        ]
        for w in tool_panel_widgets:
            w.setMinimumHeight(32)
            tool_panel.addWidget(w)

        tool_panel.addSpacing(16)
        tool_panel.addWidget(QtWidgets.QLabel("Brightness"))
        self.brightness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.brightness_slider.setRange(-50, 50)
        self.brightness_slider.setValue(0)
        tool_panel.addWidget(self.brightness_slider)

        tool_panel.addWidget(QtWidgets.QLabel("Contrast"))
        self.contrast_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.contrast_slider.setRange(-50, 50)
        self.contrast_slider.setValue(0)
        tool_panel.addWidget(self.contrast_slider)

        apply_adjust_btn = QtWidgets.QPushButton("Apply Adjustments")
        tool_panel.addWidget(apply_adjust_btn)
        tool_panel.addStretch(1)

        # Right: Preview
        self.preview = QtWidgets.QLabel()
        self.preview.setAlignment(QtCore.Qt.AlignCenter)
        self.preview.setBackgroundRole(QtGui.QPalette.Base)
        self.preview.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.preview.setStyleSheet("background:#1e1e1e; color:#ddd; border:1px solid #333;")

        # Overlay for crop rectangle feedback
        self.preview.installEventFilter(self)

        layout.addLayout(tool_panel, 0)
        layout.addWidget(self.preview, 1)

        # Connections
        open_btn.clicked.connect(self.open_image)
        save_btn.clicked.connect(self.save_image_as)
        undo_btn.clicked.connect(self.undo)
        redo_btn.clicked.connect(self.redo)
        rotate_left_btn.clicked.connect(lambda: self.rotate(-90))
        rotate_right_btn.clicked.connect(lambda: self.rotate(90))
        resize_btn.clicked.connect(self.resize_image)
        crop_btn.clicked.connect(self.toggle_crop_mode)
        grayscale_btn.clicked.connect(self.to_grayscale)
        blur_btn.clicked.connect(self.apply_blur)
        sharpen_btn.clicked.connect(self.apply_sharpen)
        apply_adjust_btn.clicked.connect(self.apply_brightness_contrast)

        self._update_buttons()

    def eventFilter(self, obj, event):
        if obj is self.preview and self.crop_mode and self.image is not None:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                self.crop_start = event.pos()
                self.crop_end = event.pos()
                self.update()
            elif event.type() == QtCore.QEvent.MouseMove and self.crop_start:
                self.crop_end = event.pos()
                self.update()
            elif event.type() == QtCore.QEvent.MouseButtonRelease and self.crop_start:
                self.crop_end = event.pos()
                self.perform_crop()
                self.crop_start = None
                self.crop_end = None
                self.crop_mode = False
                self.update()
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.crop_mode and self.crop_start and self.crop_end:
            # draw rectangle overlay on preview
            label_pos = self.preview.mapToGlobal(QtCore.QPoint(0, 0))
            win_pos = self.mapToGlobal(QtCore.QPoint(0, 0))
            offset = label_pos - win_pos
            painter = QtGui.QPainter(self)
            pen = QtGui.QPen(QtGui.QColor(0, 200, 255), 2, QtCore.Qt.DashLine)
            painter.setPen(pen)
            rect = QtCore.QRect(self.crop_start + offset, self.crop_end + offset).normalized()
            painter.drawRect(rect)
            painter.end()

    def toggle_crop_mode(self):
        if self.image is None:
            return
        self.crop_mode = not self.crop_mode
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), "Drag on preview to crop")

    def perform_crop(self):
        if not (self.image and self.crop_start and self.crop_end):
            return
        # Map preview coords to image coords
        pix = self.preview.pixmap()
        if not pix:
            return
        disp_w = pix.width()
        disp_h = pix.height()
        lbl_w = self.preview.width()
        lbl_h = self.preview.height()
        # account for aspect fit
        img_w, img_h = self.image.size
        scale = min(lbl_w / img_w, lbl_h / img_h)
        draw_w = int(img_w * scale)
        draw_h = int(img_h * scale)
        x_off = (lbl_w - draw_w) // 2
        y_off = (lbl_h - draw_h) // 2
        x1 = max(0, min(draw_w, self.crop_start.x() - x_off))
        y1 = max(0, min(draw_h, self.crop_start.y() - y_off))
        x2 = max(0, min(draw_w, self.crop_end.x() - x_off))
        y2 = max(0, min(draw_h, self.crop_end.y() - y_off))
        if x2 == x1 or y2 == y1:
            return
        # map to image coordinates
        ix1 = int(x1 / scale)
        iy1 = int(y1 / scale)
        ix2 = int(x2 / scale)
        iy2 = int(y2 / scale)
        box = (min(ix1, ix2), min(iy1, iy2), max(ix1, ix2), max(iy1, iy2))
        cropped = self.image.crop(box)
        self._apply_and_push(cropped)

    def open_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if path:
            img = Image.open(path).convert("RGBA")
            self.image = img
            self.path = path
            self.history.push(img)
            self._render()
            self._update_buttons()

    def save_image_as(self):
        if self.image is None:
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Image As", "edited.png", "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)")
        if path:
            # choose format by extension
            ext = path.split(".")[-1].lower()
            fmt = "PNG"
            if ext in ["jpg", "jpeg"]:
                fmt = "JPEG"
            elif ext == "bmp":
                fmt = "BMP"
            rgb_img = self.image.convert("RGB") if fmt in ("JPEG",) else self.image
            rgb_img.save(path, fmt)

    def _apply_and_push(self, img):
        self.image = img
        self.history.push(img)
        self._render()
        self._update_buttons()

    def _render(self):
        if self.image is None:
            self.preview.setPixmap(QtGui.QPixmap())
            return
        qimage = ImageQt.ImageQt(self.image)
        pix = QtGui.QPixmap.fromImage(qimage)
        self.preview.setPixmap(pix.scaled(self.preview.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()

    def rotate(self, angle):
        if self.image is None:
            return
        rotated = self.image.rotate(-angle, expand=True)
        self._apply_and_push(rotated)

    def resize_image(self):
        if self.image is None:
            return
        w, h = self.image.size
        w_str, ok1 = QtWidgets.QInputDialog.getInt(self, "Resize", "Width:", w, 1, 10000)
        if not ok1:
            return
        h_str, ok2 = QtWidgets.QInputDialog.getInt(self, "Resize", "Height:", h, 1, 10000)
        if not ok2:
            return
        resized = self.image.resize((w_str, h_str), Image.LANCZOS)
        self._apply_and_push(resized)

    def to_grayscale(self):
        if self.image is None:
            return
        gray = self.image.convert("L").convert("RGBA")
        self._apply_and_push(gray)

    def apply_blur(self):
        if self.image is None:
            return
        blurred = self.image.filter(ImageFilter.GaussianBlur(radius=2))
        self._apply_and_push(blurred)

    def apply_sharpen(self):
        if self.image is None:
            return
        sharp = self.image.filter(ImageFilter.SHARPEN)
        self._apply_and_push(sharp)

    def apply_brightness_contrast(self):
        if self.image is None:
            return
        b_delta = self.brightness_slider.value() / 50.0  # -1..+1
        c_delta = self.contrast_slider.value() / 50.0    # -1..+1
        img = self.image
        if b_delta != 0:
            factor = 1.0 + b_delta
            img = ImageEnhance.Brightness(img).enhance(factor)
        if c_delta != 0:
            factor = 1.0 + c_delta
            img = ImageEnhance.Contrast(img).enhance(factor)
        self._apply_and_push(img)
        # reset sliders
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)

    def undo(self):
        prev = self.history.undo()
        if prev is not None:
            self.image = prev
            self._render()
            self._update_buttons()

    def redo(self):
        nxt = self.history.redo()
        if nxt is not None:
            self.image = nxt
            self._render()
            self._update_buttons()

    def _update_buttons(self):
        self.statusBar().showMessage(
            f"Size: {self.image.size if self.image else '-'} | Undo: {self.history.can_undo()} | Redo: {self.history.can_redo()}"
        )


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = ImageEditor()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
