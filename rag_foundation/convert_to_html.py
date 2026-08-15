import os
import sys
from pathlib import Path
import win32com.client
import time

def convert_to_html(input_dir, output_dir):
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()
    
    if not output_path.exists():
        output_path.mkdir(parents=True)
        
    try:
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False
        word.DisplayAlerts = False
    except Exception as e:
        print(f"Error starting Word: {e}")
        return
        
    files = list(input_path.glob('*.*'))
    valid_exts = {'.doc', '.docx', '.pdf'}
    
    for file in files:
        if file.suffix.lower() not in valid_exts:
            continue
            
        print(f"Converting: {file.name}")
        out_file = output_path / f"{file.stem}.html"
        
        try:
            # Open document
            doc = word.Documents.Open(str(file), ConfirmConversions=False, ReadOnly=True)
            # wdFormatHTML = 8, wdFormatFilteredHTML = 10
            doc.SaveAs2(str(out_file), FileFormat=10)
            doc.Close()
            print(f"  -> Success: {out_file.name}")
        except Exception as e:
            print(f"  -> Failed: {e}")
            
    try:
        word.Quit()
    except:
        pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_to_html.py <input_dir> <output_dir>")
        sys.exit(1)
    convert_to_html(sys.argv[1], sys.argv[2])
