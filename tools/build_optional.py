"""Generate the explicitly unexecuted PySCF extension notebook."""
from pathlib import Path
import nbformat as n

root=Path(__file__).resolve().parents[1]
book=n.v4.new_notebook()
book.cells=[
 n.v4.new_markdown_cell("# Дополнение к ЛР 12: PySCF DFT\n\nНе выполнено в проверенной native Windows-среде. Требуется поддерживаемая среда PySCF. Основная ЛР 12 выполняет RHF и проверена отдельно. Прочитайте README в этой папке."),
 n.v4.new_code_cell('''from pathlib import Path
import sys
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/"Labs/pyscf_dft.py").exists())
sys.path.insert(0,str(ROOT/"Labs"))
from pyscf_dft import run
result=run(ROOT/"Labs/results/dft")
print(result)
assert result["HF_converged"] and result["DFT_converged"]
assert abs(result["RHF_energy_hartree"]+1.116759307)<5e-5
assert result["functional"]=="PBE"
'''),
 n.v4.new_markdown_cell("Сравните методы при одинаковом базисе и геометрии. Почему ни одно число не является свободной энергией реакции? Не копируйте готовый DFT-результат вместо исполнения.")]
book.metadata={"kernelspec":{"name":"python3","display_name":"Python 3","language":"python"}}
n.write(book,root/'Labs/extensions/dft_pyscf.ipynb')
