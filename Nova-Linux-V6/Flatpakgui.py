import subprocess
import customtkinter as ctk

# Function to run the Flatpak command and show output
def run_flatpak_command():
    try:
        result = subprocess.run(["flatpak", "list"], capture_output=True, text=True)
        output_textbox.delete("1.0", "end")  # Clear previous output
        output_textbox.insert("1.0", result.stdout if result.stdout else result.stderr)
    except Exception as e:
        output_textbox.insert("1.0", f"Error running command: {e}")

# Initialize CustomTkinter app
ctk.set_appearance_mode("System")  # Or "Dark"/"Light"
ctk.set_default_color_theme("blue")  # Optional

app = ctk.CTk()
app.geometry("600x400")
app.title("Flatpak Command Output")

# Add button to trigger command
run_button = ctk.CTkButton(app, text="Run Flatpak Command", command=run_flatpak_command)
run_button.pack(pady=10)

# Add text box to display command output
output_textbox = ctk.CTkTextbox(app, width=580, height=300)
output_textbox.pack(pady=10)

# Run the app
app.mainloop()
