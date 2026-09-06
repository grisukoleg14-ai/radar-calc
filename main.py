import io
import math
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Импорты Kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window

# Светло-серый фон окна
Window.clearcolor = (0.95, 0.95, 0.95, 1)

class RadarApp(App):
    def build(self):
        root = ScrollView(size_hint=(1, 1), bar_width=10)
        self.main_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=15, padding=20)
        self.main_layout.bind(minimum_height=self.main_layout.setter("height"))

        intro_text = (
            "Данное приложение в реальном времени рассчитывает предельную дальность РЛС "
            "по основному уравнению радиолокации:\n\n"
            "                     R_max = [ (Pt * G² * λ² * σ) / ((4π)³ * Pmin) ]^(1/4)\n\n"
            "Инструкция: Изменяйте любые параметры в полях ниже. Расчет и все три графика "
            "обновляются автоматически прямо в процессе ввода.\n\n"
            "Описание физических величин:\n"
            "• Pt — импульсная мощность передатчика (Вт)\n"
            "• G — коэф. усиления антенны (в разах)\n"
            "• λ (Длина волны) — рабочая длина волны РЛС (м)\n"
            "• σ (ЭПР) — эффективная площадь рассеяния цели (кв.м)\n"
            "• Pmin — чувствительность приемного устройства (Вт)"
        )

        lbl_intro = Label(
            text=intro_text, size_hint_y=None, halign="left", valign="top",
            color=(0.15, 0.15, 0.15, 1), font_size="14sp"
        )
        lbl_intro.bind(texture_size=lambda instance, value: setattr(instance, "height", value[1]))
        lbl_intro.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
        self.main_layout.add_widget(lbl_intro)

        self.inputs = {}
        fields = [
            ("Мощность Pt, Вт", "10000", "Pt"),
            ("Коэф. усиления G, раз", "1000", "G"),
            ("Длина волны λ, м", "6", "lambda"),
            ("ЭПР цели σ, кв.м", "1.0", "sigma"),
            ("Порог Pmin, Вт", "1e-12", "Pmin"),
        ]

        for label_text, default_val, key in fields:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=40)
            lbl = Label(text=label_text, size_hint_x=0.6, halign="left", color=(0.15, 0.15, 0.15, 1))
            lbl.bind(width=lambda instance, value: setattr(instance, "text_size", (value, None)))
            
            txt_input = TextInput(text=default_val, multiline=False, input_filter="float", size_hint_x=0.4)
            txt_input.bind(text=self.on_text_change)
            row.add_widget(lbl)
            row.add_widget(txt_input)
            self.main_layout.add_widget(row)
            self.inputs[key] = txt_input

        btn_calc = Button(text="Рассчитать и обновить графики", size_hint_y=None, height=50, background_color=(0.1, 0.5, 0.1, 1))
        btn_calc.bind(on_press=self.calculate_and_plot)
        self.main_layout.add_widget(btn_calc)

        self.lbl_result = Label(text="Макс. дальность: —", font_size="16sp", bold=True, size_hint_y=None, height=40, color=(0.1, 0.5, 0.1, 1))
        self.main_layout.add_widget(self.lbl_result)

        self.graph_image = Image(size_hint_y=None, height=900)
        self.main_layout.add_widget(self.graph_image)

        root.add_widget(self.main_layout)
        self.calculate_and_plot(None)
        return root

    def on_text_change(self, instance, value):
        self.calculate_and_plot(None)

    def calculate_and_plot(self, instance):
        try:
            P_t_text = self.inputs["Pt"].text
            G_text = self.inputs["G"].text
            lam_text = self.inputs["lambda"].text
            sigma_text = self.inputs["sigma"].text
            P_min_text = self.inputs["Pmin"].text

            if not (P_t_text and G_text and lam_text and sigma_text and P_min_text):
                return

            P_t = float(P_t_text)
            G = float(G_text)
            lam = float(lam_text)
            sigma = float(sigma_text)
            P_min = float(P_min_text)

            if P_t <= 0 or G <= 0 or lam <= 0 or sigma <= 0 or P_min <= 0:
                self.lbl_result.text = "Параметры должны быть > 0"
                self.lbl_result.color = (0.8, 0.1, 0.1, 1)
                return

            numerator = P_t * (G**2) * (lam**2) * sigma
            denominator = ((4 * math.pi) ** 3) * P_min
            R_max = (numerator / denominator) ** 0.25

            self.lbl_result.text = f"Макс. дальность: {R_max:.2f} м ({R_max/1000:.3f} км)"
            self.lbl_result.color = (0.1, 0.5, 0.1, 1)

            def calc_R_km(P, s):
                num = P * (G**2) * (lam**2) * s
                den = ((4 * math.pi) ** 3) * P_min
                return ((num / den) ** 0.25) / 1000.0

            P_range = np.linspace(0.1 * P_t, 3.0 * P_t, 100)
            sigma_range = np.linspace(0.1 * sigma, 3.0 * sigma, 100)
            R_current = calc_R_km(P_t, sigma)

            fig = plt.figure(figsize=(6, 12), dpi=100)
            fig.patch.set_facecolor("#f2f2f2")

            ax1 = fig.add_subplot(3, 1, 1)
            ax1.set_facecolor("#ffffff")
            ax1.plot(P_range, calc_R_km(P_range, sigma), color="blue", lw=2)
            ax1.scatter(P_t, R_current, color="red", s=40, zorder=5)
            ax1.set_title("1. Дальность от мощности Pt")
            ax1.set_xlabel("Мощность Pt (Вт)")
            ax1.set_ylabel("Дальность R (км)")
            ax1.grid(True)

            ax2 = fig.add_subplot(3, 1, 2)
            ax2.set_facecolor("#ffffff")
            ax2.plot(sigma_range, calc_R_km(P_t, sigma_range), color="green", lw=2)
            ax2.scatter(sigma, R_current, color="red", s=40, zorder=5)
            ax2.set_title("2. Дальность от ЭПР цели (σ)")
            ax2.set_xlabel("ЭПР σ (м²)")
            ax2.set_ylabel("Дальность R (км)")
            ax2.grid(True)

            ax3 = fig.add_subplot(3, 1, 3, projection="3d")
            ax3.set_facecolor("#f2f2f2")
            P_grid, sigma_grid = np.meshgrid(np.linspace(0.1 * P_t, 3.0 * P_t, 30), np.linspace(0.1 * sigma, 3.0 * sigma, 30))
            R_grid = calc_R_km(P_grid, sigma_grid)
            ax3.plot_surface(P_grid, sigma_grid, R_grid, cmap="viridis", edgecolor="none")
            ax3.scatter(P_t, sigma, R_current, color="red", s=50, depthshade=False, label="Рабочая точка")
            ax3.set_title("3. Зависимость R от ЭПР и Pt")
            ax3.set_xlabel("Pt (Вт)", fontsize=8)
            ax3.set_ylabel("σ (м²)", fontsize=8)
            ax3.set_zlabel("R (км)", fontsize=8)

            fig.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format="png", facecolor=fig.get_facecolor(), edgecolor="none")
            buf.seek(0)
            plt.close(fig)

            im = CoreImage(buf, ext="png")
            self.graph_image.texture = im.texture

        except Exception as e:
            self.lbl_result.text = f"Ошибка данных: {str(e)}"
            self.lbl_result.color = (0.8, 0.1, 0.1, 1)

if __name__ == "__main__":
    RadarApp().run()
