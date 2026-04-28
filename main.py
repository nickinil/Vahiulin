import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import requests
except ImportError:
    requests = None


API_KEY = "YOUR_API_KEY"
HISTORY_FILE = "history.json"

CURRENCIES = ["USD", "EUR", "RUB", "GBP", "CNY", "JPY", "TRY", "KZT"]


class CurrencyConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("850x560")
        self.root.resizable(False, False)

        self.history = []
        self.load_history()
        self.create_widgets()
        self.update_history_table()

    def create_widgets(self):
        title = tk.Label(
            self.root,
            text="Currency Converter — Конвертер валют",
            font=("Arial", 18, "bold")
        )
        title.pack(pady=10)

        form_frame = tk.Frame(self.root)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Сумма:", font=("Arial", 11)).grid(row=0, column=0, padx=5, pady=5)
        self.amount_entry = tk.Entry(form_frame, width=18)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Из валюты:", font=("Arial", 11)).grid(row=0, column=2, padx=5, pady=5)
        self.from_currency = ttk.Combobox(form_frame, values=CURRENCIES, state="readonly", width=10)
        self.from_currency.set("USD")
        self.from_currency.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="В валюту:", font=("Arial", 11)).grid(row=0, column=4, padx=5, pady=5)
        self.to_currency = ttk.Combobox(form_frame, values=CURRENCIES, state="readonly", width=10)
        self.to_currency.set("RUB")
        self.to_currency.grid(row=0, column=5, padx=5, pady=5)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        tk.Button(
            button_frame,
            text="Конвертировать",
            width=18,
            command=self.convert_currency
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            button_frame,
            text="Загрузить историю",
            width=18,
            command=self.load_history_button
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            button_frame,
            text="Очистить историю",
            width=18,
            command=self.clear_history
        ).grid(row=0, column=2, padx=5)

        self.result_label = tk.Label(
            self.root,
            text="Результат появится здесь",
            font=("Arial", 13, "bold")
        )
        self.result_label.pack(pady=10)

        table_frame = tk.Frame(self.root)
        table_frame.pack(pady=10)

        columns = ("date", "amount", "from", "to", "result", "rate")
        self.history_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=13)

        self.history_table.heading("date", text="Дата и время")
        self.history_table.heading("amount", text="Сумма")
        self.history_table.heading("from", text="Из")
        self.history_table.heading("to", text="В")
        self.history_table.heading("result", text="Результат")
        self.history_table.heading("rate", text="Курс")

        self.history_table.column("date", width=170)
        self.history_table.column("amount", width=100)
        self.history_table.column("from", width=70)
        self.history_table.column("to", width=70)
        self.history_table.column("result", width=120)
        self.history_table.column("rate", width=120)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.history_table.yview)
        self.history_table.configure(yscrollcommand=scrollbar.set)

        self.history_table.grid(row=0, column=0)
        scrollbar.grid(row=0, column=1, sticky="ns")

        info = tk.Label(
            self.root,
            text="Для работы с актуальными курсами укажите API_KEY в коде. При ошибке API используются резервные курсы.",
            fg="gray"
        )
        info.pack(pady=5)

    def validate_amount(self, value):
        try:
            amount = float(value.replace(",", "."))
        except ValueError:
            raise ValueError("Сумма должна быть числом.")

        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом.")

        return amount

    def get_rate_from_api(self, from_code, to_code):
        if from_code == to_code:
            return 1.0

        if requests is None:
            raise RuntimeError("Библиотека requests не установлена.")

        if API_KEY == "YOUR_API_KEY":
            raise RuntimeError("API-ключ не указан.")

        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{from_code}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("result") != "success":
            raise RuntimeError("API вернул ошибку.")

        rates = data.get("conversion_rates", {})
        if to_code not in rates:
            raise RuntimeError("Выбранная валюта не найдена в ответе API.")

        return float(rates[to_code])

    def get_fallback_rate(self, from_code, to_code):
        fallback_rates_to_usd = {
            "USD": 1.0,
            "EUR": 1.08,
            "RUB": 0.011,
            "GBP": 1.25,
            "CNY": 0.14,
            "JPY": 0.0067,
            "TRY": 0.031,
            "KZT": 0.0022
        }

        if from_code == to_code:
            return 1.0

        from_to_usd = fallback_rates_to_usd[from_code]
        to_to_usd = fallback_rates_to_usd[to_code]
        return from_to_usd / to_to_usd

    def convert_currency(self):
        try:
            amount = self.validate_amount(self.amount_entry.get().strip())
            from_code = self.from_currency.get()
            to_code = self.to_currency.get()

            try:
                rate = self.get_rate_from_api(from_code, to_code)
                source = "API"
            except Exception:
                rate = self.get_fallback_rate(from_code, to_code)
                source = "резервный курс"

            result = round(amount * rate, 2)

            self.result_label.config(
                text=f"{amount:.2f} {from_code} = {result:.2f} {to_code} ({source})"
            )

            record = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "amount": round(amount, 2),
                "from_currency": from_code,
                "to_currency": to_code,
                "result": result,
                "rate": round(rate, 6)
            }

            self.history.append(record)
            self.save_history()
            self.update_history_table()

        except ValueError as error:
            messagebox.showerror("Ошибка ввода", str(error))
        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось выполнить конвертацию: {error}")

    def update_history_table(self):
        for item in self.history_table.get_children():
            self.history_table.delete(item)

        for record in self.history:
            self.history_table.insert(
                "",
                tk.END,
                values=(
                    record.get("date", ""),
                    record.get("amount", ""),
                    record.get("from_currency", ""),
                    record.get("to_currency", ""),
                    record.get("result", ""),
                    record.get("rate", "")
                )
            )

    def save_history(self):
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump(self.history, file, ensure_ascii=False, indent=2)

    def load_history(self):
        if not os.path.exists(HISTORY_FILE):
            self.history = []
            return

        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as file:
                self.history = json.load(file)
        except (json.JSONDecodeError, OSError):
            self.history = []

    def load_history_button(self):
        self.load_history()
        self.update_history_table()
        messagebox.showinfo("Загрузка", "История загружена из JSON-файла.")

    def clear_history(self):
        if not self.history:
            messagebox.showinfo("Информация", "История уже пуста.")
            return

        answer = messagebox.askyesno("Подтверждение", "Очистить всю историю?")
        if answer:
            self.history = []
            self.save_history()
            self.update_history_table()
            self.result_label.config(text="История очищена.")


if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverterApp(root)
    root.mainloop()
