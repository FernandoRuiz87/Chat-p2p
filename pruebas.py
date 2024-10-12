import tkinter as tk


def main():
    root = tk.Tk()
    text_widget = tk.Text(root, height=2, width=30)
    text_widget.pack()

    # Insert text with different tags
    text_widget.insert(tk.END, "Texto en ", "rojo")
    text_widget.insert(tk.END, "una misma ", "verde")
    text_widget.insert(tk.END, "línea.", "azul")

    # Configure tags with different colors
    text_widget.tag_config("rojo", foreground="red")
    text_widget.tag_config("verde", foreground="green")
    text_widget.tag_config("azul", foreground="blue")

    root.mainloop()


if __name__ == "__main__":
    main()
