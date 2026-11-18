"""Call the installed skill using PyMuPDF4LLM's legacy text layout engine."""
import runpy
import sys
import pymupdf4llm

pymupdf4llm.use_layout(False)
skill, *arguments = sys.argv[1:]
sys.argv = [skill, *arguments]
runpy.run_path(skill, run_name="__main__")
