import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar, Style
import threading
import queue

# Dicionário de traduções
translations = {
    'pt': {
        'title': "Caminho do Código",
        'folder_label': "Pastas do Projeto (separadas por ';'):",
        'output_label': "Nome do Arquivo de Saída:",
        'output_format_label': "Formato de Saída:",
        'extensions_label': "Extensões de Arquivo a Incluir (separadas por ','):",
        'extensions_info': "Insira extensões para incluir apenas esses arquivos na análise (ex: py,html). Deixe em branco para incluir todos os arquivos.",
        'ignore_git': "Ignorar arquivos do Git (.git)",
        'recursive': "Análise Recursiva",
        'recursive_info': "Se habilitado, a análise incluirá subpastas do projeto.",
        'output_type_label': "Tipo de Saída da Análise:",
        'program_structure': "Estrutura para Programador (apenas hierarquia)",
        'complete_structure': "Estrutura Completa (detalhes dos arquivos)",
        'ai_structure': "Estrutura para IA (JSON)",
        'analyze_button': "Analisar Projeto",
        'exit_button': "Sair",
        'success_title': "Sucesso",
        'success_message': "A estrutura do projeto foi salva em {}",
        'error_title': "Erro",
        'error_message': "Ocorreu um erro: {}",
        'input_error': "Por favor, preencha todos os campos.",
    },
    'en': {
        'title': "Code Path",
        'folder_label': "Project Folders (separated by ';'):",
        'output_label': "Output File Name:",
        'output_format_label': "Output Format:",
        'extensions_label': "File Extensions to Include (separated by ','):",
        'extensions_info': "Enter extensions to include only these files in the analysis (e.g., py,html). Leave blank to include all files.",
        'ignore_git': "Ignore Git files (.git)",
        'recursive': "Recursive Analysis",
        'recursive_info': "If enabled, the analysis will include subfolders of the project.",
        'output_type_label': "Output Type of the Analysis:",
        'program_structure': "Structure for Programmer (only hierarchy)",
        'complete_structure': "Complete Structure (file details)",
        'ai_structure': "Structure for AI (JSON)",
        'analyze_button': "Analyze Project",
        'exit_button': "Exit",
        'success_title': "Success",
        'success_message': "The project structure has been saved in {}",
        'error_title': "Error",
        'error_message': "An error occurred: {}",
        'input_error': "Please fill in all fields.",
    }
}

# Inicializa a Interface Gráfica
root = tk.Tk()
root.title(translations['pt']['title'])

# Variáveis e elementos globais
output_queue = queue.Queue()  # Fila para comunicar progresso entre threads
progress_var = tk.DoubleVar()  # Variável para a barra de progresso
selected_language = tk.StringVar(value='pt')  # Variável para o idioma selecionado

class ProjectAnalyzer:
    def __init__(self):
        self.history = []

    def analyze_project_folders(self, folder_paths, output_file, ignore_git, include_extensions, recursive, output_type):
        """
        Analisa as pastas do projeto, gerando a estrutura de arquivos e detalhes.
        """
        try:
            total_files = self.count_files(folder_paths, ignore_git)
            processed_files = 0
            structure, content_details = [], []

            for folder_path in folder_paths:
                for root_dir, dirs, files in os.walk(folder_path):
                    if ignore_git and '.git' in dirs:
                        dirs.remove('.git')

                    relative_path = os.path.relpath(root_dir, folder_path)
                    relative_path = 'Pasta Raiz' if relative_path == '.' else relative_path
                    structure.append(f"{relative_path}/")

                    for file in files:
                        if self.should_include_file(file, include_extensions):
                            file_path = os.path.join(root_dir, file)
                            processed_files += 1
                            structure.append(f"    └── {file}")
                            
                            if output_type != "Programador":
                                self.read_file_content(file_path, content_details)

                            # Atualiza o progresso
                            output_queue.put((processed_files / total_files) * 100)

            # Salva os resultados no formato escolhido
            self.save_output(output_file, structure, content_details, output_type)
            self.history.append(output_file)
            messagebox.showinfo(translations[selected_language.get()]['success_title'], 
                                translations[selected_language.get()]['success_message'].format(output_file))

        except Exception as e:
            messagebox.showerror(translations[selected_language.get()]['error_title'], 
                                 translations[selected_language.get()]['error_message'].format(str(e)))
        finally:
            button_analyze.config(state=tk.NORMAL)
            progress_var.set(100)  # Define a barra como completa ao final

    def count_files(self, folder_paths, ignore_git):
        """ Conta o número total de arquivos a serem processados. """
        return sum(len(files) for folder_path in folder_paths for _, dirs, files in os.walk(folder_path) if not (ignore_git and '.git' in dirs))

    def should_include_file(self, file, include_extensions):
        """ Verifica se o arquivo deve ser incluído na análise. """
        if include_extensions:
            return any(file.endswith(ext) for ext in include_extensions)
        return not file.endswith('.pyc')  # Ignora arquivos binários

    def read_file_content(self, file_path, content_details):
        """ Lê o conteúdo do arquivo e adiciona detalhes à lista. """
        try:
            with open(file_path, 'r', encoding='utf-8') as file_content:
                content = file_content.read()
                content_details.append({"file": file_path, "content": content})
        except Exception as e:
            content_details.append(f"\nArquivo: {file_path}\nErro ao ler o arquivo: {str(e)}\n")

    def save_output(self, output_file, structure, content_details, output_type):
        """ Salva a saída no formato especificado. """
        with open(output_file, 'w', encoding='utf-8') as f:
            if output_type == "AI":
                json.dump({"estrutura_do_projeto": structure, "detalhes_dos_arquivos": content_details}, f, indent=4)
            else:
                f.write("Estrutura do Projeto:\n")
                f.write("\n".join(structure) + "\n\n")
                if output_type == "Completa":
                    f.write("Detalhes dos Arquivos:\n")
                    f.write(json.dumps(content_details, indent=4))


def update_progress_bar():
    """ Atualiza a barra de progresso a partir da fila de saída. """
    try:
        while True:
            progress = output_queue.get_nowait()
            progress_var.set(progress)
            root.update_idletasks()
    except queue.Empty:
        pass
    root.after(100, update_progress_bar)  # Atualiza a cada 100 ms

# Funções da GUI
def select_folders():
    """ Permite ao usuário selecionar pastas para análise. """
    folder_path = filedialog.askdirectory()
    if folder_path:
        current_folders = entry_folder.get()
        entry_folder.delete(0, tk.END)
        entry_folder.insert(0, f"{current_folders};{folder_path}" if current_folders else folder_path)


def analyze():
    """ Inicia a análise do projeto. """
    folder_paths = entry_folder.get().split(";")
    output_file = entry_output.get()

    output_file += f".{var_output_format.get()}"

    ignore_git = var_ignore_git.get()
    include_extensions = entry_extensions.get().split(",") if entry_extensions.get() else None
    recursive = var_recursive.get()
    output_type = var_output_type.get()

    if folder_paths and output_file:
        button_analyze.config(state=tk.DISABLED)
        progress_var.set(0)
        threading.Thread(target=project_analyzer.analyze_project_folders,
                         args=(folder_paths, output_file, ignore_git, include_extensions, recursive, output_type)).start()
    else:
        messagebox.showwarning("Input Error", translations[selected_language.get()]['input_error'])

def exit_program():
    """ Encerra o programa. """
    root.destroy()

# Função para atualizar a interface com base no idioma
def update_language():
    lang = selected_language.get()
    root.title(translations[lang]['title'])
    label_folder.config(text=translations[lang]['folder_label'])
    label_output.config(text=translations[lang]['output_label'])
    label_format.config(text=translations[lang]['output_format_label'])
    label_extensions.config(text=translations[lang]['extensions_label'])
    label_extensions_info.config(text=translations[lang]['extensions_info'])
    checkbox_ignore_git.config(text=translations[lang]['ignore_git'])
    checkbox_recursive.config(text=translations[lang]['recursive'])
    label_recursive_info.config(text=translations[lang]['recursive_info'])
    label_output_type.config(text=translations[lang]['output_type_label'])
    radio_program_structure.config(text=translations[lang]['program_structure'])
    radio_complete_structure.config(text=translations[lang]['complete_structure'])
    radio_ai_structure.config(text=translations[lang]['ai_structure'])
    button_analyze.config(text=translations[lang]['analyze_button'])
    button_exit.config(text=translations[lang]['exit_button'])

# Inicializa o projeto
project_analyzer = ProjectAnalyzer()

# Configuração da interface
frame_inputs = tk.Frame(root)
frame_inputs.pack(pady=10)

# Pastas do Projeto
label_folder = tk.Label(frame_inputs, text=translations['pt']['folder_label'])
label_folder.grid(row=0, column=0)
entry_folder = tk.Entry(frame_inputs, width=50)
entry_folder.grid(row=0, column=1)
button_select_folder = tk.Button(frame_inputs, text="Selecionar Pastas", command=select_folders)
button_select_folder.grid(row=0, column=2)

# Nome do Arquivo de Saída
label_output = tk.Label(frame_inputs, text=translations['pt']['output_label'])
label_output.grid(row=1, column=0)
entry_output = tk.Entry(frame_inputs, width=50)
entry_output.grid(row=1, column=1)

# Formato de Saída
label_format = tk.Label(frame_inputs, text=translations['pt']['output_format_label'])
label_format.grid(row=2, column=0)
var_output_format = tk.StringVar(value='json')
output_format_menu = tk.OptionMenu(frame_inputs, var_output_format, 'json', 'txt', 'md')
output_format_menu.grid(row=2, column=1)

# Extensões de Arquivo
label_extensions = tk.Label(frame_inputs, text=translations['pt']['extensions_label'])
label_extensions.grid(row=3, column=0)
entry_extensions = tk.Entry(frame_inputs, width=50)
entry_extensions.grid(row=3, column=1)
label_extensions_info = tk.Label(frame_inputs, text=translations['pt']['extensions_info'])
label_extensions_info.grid(row=4, column=0, columnspan=3)

# Ignorar arquivos do Git
var_ignore_git = tk.BooleanVar()
checkbox_ignore_git = tk.Checkbutton(frame_inputs, text=translations['pt']['ignore_git'], variable=var_ignore_git)
checkbox_ignore_git.grid(row=5, column=0, columnspan=2)

# Análise Recursiva
var_recursive = tk.BooleanVar()
checkbox_recursive = tk.Checkbutton(frame_inputs, text=translations['pt']['recursive'], variable=var_recursive)
checkbox_recursive.grid(row=6, column=0, columnspan=2)
label_recursive_info = tk.Label(frame_inputs, text=translations['pt']['recursive_info'])
label_recursive_info.grid(row=7, column=0, columnspan=3)

# Tipo de Saída
label_output_type = tk.Label(frame_inputs, text=translations['pt']['output_type_label'])
label_output_type.grid(row=8, column=0)
var_output_type = tk.StringVar(value='Programador')
radio_program_structure = tk.Radiobutton(frame_inputs, text=translations['pt']['program_structure'], variable=var_output_type, value='Programador')
radio_program_structure.grid(row=8, column=1)
radio_complete_structure = tk.Radiobutton(frame_inputs, text=translations['pt']['complete_structure'], variable=var_output_type, value='Completa')
radio_complete_structure.grid(row=8, column=2)
radio_ai_structure = tk.Radiobutton(frame_inputs, text=translations['pt']['ai_structure'], variable=var_output_type, value='AI')
radio_ai_structure.grid(row=8, column=3)

# Botões
button_frame = tk.Frame(root)
button_frame.pack(pady=10)
button_analyze = tk.Button(button_frame, text=translations['pt']['analyze_button'], command=analyze)
button_analyze.grid(row=0, column=0)
button_exit = tk.Button(button_frame, text=translations['pt']['exit_button'], command=exit_program)
button_exit.grid(row=0, column=1)

# Barra de progresso
style = Style()
style.configure("TProgressbar", thickness=20)
progressbar = Progressbar(root, variable=progress_var, style="TProgressbar", maximum=100)
progressbar.pack(pady=20, fill=tk.X, padx=20)

# Seletor de Idioma
language_frame = tk.Frame(root)
language_frame.pack(pady=5)
tk.Radiobutton(language_frame, text="Português", variable=selected_language, value='pt', command=update_language).pack(side=tk.LEFT)
tk.Radiobutton(language_frame, text="English", variable=selected_language, value='en', command=update_language).pack(side=tk.LEFT)

# Atualização da interface inicial
update_language()

# Início da atualização da barra de progresso
update_progress_bar()

# Inicia o loop da interface
root.mainloop()
