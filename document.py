# handles everything related to documents 
# when you want to support a new file type, add it here 

from rich.console import Console

console = Console()

def load_document(filepath):
    """ 
    Reads a file and returns its contest as a string.
    Supports: txt, pdf, xlsx, xls, csv

    """

    # get file extension 
    extension = filepath.split(".")[-1].lower()

    try:
        if extension == "txt":
            return load_txt(filepath)

        elif extension == "pdf":
            return load_pdf(filepath)

        elif extension in ["xls", "xlsx", "csv"]:
            return load_spreadsheet(filepath, extension)

        else:
            console.print(f"[red] Unsupported file type: {extension}[/red]")
            console.print("[dim] Supported file type: txt,pdf, xls, xlsx, csv[/dim]")
            return None

    except FileNotFoundError:
        console.print(f"[red] File not found: {filepath}[/red]")
        return None

    except Exception as e:
        console.print(f"[red] Error reading file: {e}[/red]")
        return None


def load_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content =  f.read()
    console.print(f"[green] Loaded: {filepath}[/green]")
    return content

def load_pdf(filepath):
    import fitz
    import re
    
    doc = fitz.open(filepath)
    pages_content = []
    
    for page in doc:
        # Try words-based extraction which preserves positions
        words = page.get_text("words")
        
        if not words:
            continue
            
        # Sort words by vertical position then horizontal
        # This reconstructs reading order properly
        words_sorted = sorted(words, key=lambda w: (round(w[1]/10)*10, w[0]))
        
        # Group words on same line together
        lines = {}
        for word in words_sorted:
            y_key = round(word[1] / 10) * 10
            if y_key not in lines:
                lines[y_key] = []
            lines[y_key].append(word[4])
        
        # Join lines
        page_text = ""
        for y_key in sorted(lines.keys()):
            line = " ".join(lines[y_key])
            page_text += line + "\n"
        
        pages_content.append(f"--- PAGE {page.number + 1} ---\n{page_text}")
    
    page_count = len(doc)
    doc.close()
    
    content = "\n".join(pages_content)
    
    # Clean up
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    console.print(f"[green]✓ Loaded PDF: {filepath} ({page_count} pages)[/green]")
    print(f">>> Total PDF characters: {len(content)}")
    print(f">>> Sample: {content[:300]}")
    
    return content
    


def load_spreadsheet(filepath, extension):
    import pandas as pd
    if extension == "csv":
        df = pd.read_csv(filepath)

    else:
        df = pd.read_excel(filepath)

    content = df.to_string()
    console.print(f"[green] Loaded spreadsheet: {filepath}[/green]")
    return content

