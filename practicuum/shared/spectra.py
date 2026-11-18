"""Чтение конкретного простого JCAMP-DX NIST; не универсальный парсер всех сжатых форматов."""
from pathlib import Path
import math

def read_nist_ir(path):
    metadata={};values=[];started=False
    for line in Path(path).read_text(encoding='ascii').splitlines():
        if line.startswith('##'):
            key,_,value=line[2:].partition('=');metadata[key.strip()]=value.strip()
            if key=='XYDATA':
                if value!='(X++(Y..Y))':raise ValueError('Неподдерживаемый формат XYDATA')
                started=True
            elif key=='END':break
            continue
        if not started or not line.strip():continue
        # Эта версия файла хранит несжатые числа: первое — x, остальные — последовательные y.
        numbers=[float(token) for token in line.split()]
        expected=float(metadata['FIRSTX'])+len(values)*float(metadata['DELTAX'])
        if not math.isclose(numbers[0],expected,abs_tol=1e-8):raise ValueError('Нарушена сетка JCAMP')
        values.extend(numbers[1:])
    if metadata.get('XUNITS')!='1/CM' or metadata.get('YUNITS')!='ABSORBANCE':raise ValueError('Неожиданные единицы спектра')
    if len(values)!=int(metadata['NPOINTS']):raise ValueError('Неполное число точек спектра')
    first=float(metadata['FIRSTX']);step=float(metadata['DELTAX']);factor=float(metadata['YFACTOR'])
    x=[first+i*step for i in range(len(values))];y=[v*factor for v in values]
    if not math.isclose(x[-1],float(metadata['LASTX']),abs_tol=1e-8):raise ValueError('Последняя точка не совпала')
    return {'wavenumber_cm1':x,'absorbance':y,'metadata':metadata}
