"""
voir_lettres.py — Ouvre le dossier des lettres de motivation
"""
import os
import sys
import subprocess
from pathlib import Path


def open_letters_folder(config=None, default_dir=None):
    """Ouvre le dossier des lettres dans l'explorateur natif.
    
    Args:
        config: dict config (optionnel, utilise _letters_dir si présent)
        default_dir: Path par défaut si pas configuré
    """
    if default_dir is None:
        default_dir = Path("lettres")
    
    # Utilise le chemin configuré ou le défaut
    folder = default_dir
    if config:
        custom = config.get("_letters_dir", "")
        if custom and Path(custom).exists():
            folder = Path(custom)
    
    folder.mkdir(parents=True, exist_ok=True)
    folder_abs = folder.resolve()
    
    print(f"\n  📂 Dossier lettres :")
    print(f"  {folder_abs}")
    
    # Ouvre le dossier
    try:
        if sys.platform == 'win32':
            os.startfile(str(folder_abs))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(folder_abs)], check=True)
        else:
            subprocess.run(['xdg-open', str(folder_abs)], check=True)
        print(f"  ✓ Dossier ouvert")
    except Exception:
        print(f"  (copiez le chemin ci-dessus dans votre explorateur)")
    
    # Liste le contenu
    contents = sorted(folder.glob('*'))
    if contents:
        print(f"\n  {len(contents)} fichier(s) dans ce dossier :")
        for f in contents[:20]:
            size = f.stat().st_size
            if size > 1024:
                size_str = f"{size/1024:.1f} Ko"
            else:
                size_str = f"{size} o"
            print(f"    • {f.name} ({size_str})")
        if len(contents) > 20:
            print(f"    ... et {len(contents) - 20} autres")
    else:
        print(f"\n  (dossier vide — générez des lettres avec [7])")
    print()
