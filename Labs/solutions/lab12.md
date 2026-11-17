# Ключ преподавателя: модуль 12

Решения самостоятельных кейсов. Открывать после собственной попытки. Численная проверка не оценивает научную интерпретацию; IDE-кейсы требуют запуска приложения и рецензии.


## M12-C1. Знак разности электронных энергий

Сравнимость состава, метода и базиса обязательна; разность двух минимумов не задаёт переходное состояние.


```python
case_input = {'E_initial': -100.0, 'E_final': -100.01, 'kJ_per_Hartree': 2625.5}
answer={'delta_kJ_mol':(case_input['E_final']-case_input['E_initial'])*case_input['kJ_per_Hartree']}
```


Ожидаемый численный контракт: `{"delta_kJ_mol": -26.255}`.


## M12-C2. Повтор HF/DFT при новой геометрии

Автотест проверяет только численный контракт; сами энергии, параметры и интерпретацию проверяют по артефактам.


```python
case_input = {'distance_angstrom': 1.0, 'basis': 'sto-3g', 'charge': 0, 'spin': 0, 'functional': 'PBE', 'grid_level': 4}
from pyscf import gto,scf,dft
m=gto.M(atom=f"H 0 0 0; H 0 0 {case_input['distance_angstrom']}",unit='Angstrom',basis='sto-3g',charge=0,spin=0,verbose=0);hf=scf.RHF(m);hf.conv_tol=1e-10;eh=hf.kernel();ks=dft.RKS(m);ks.xc='PBE';ks.grids.level=4;ks.conv_tol=1e-10;ed=ks.kernel();answer={'hf_converged':bool(hf.converged),'pbe_converged':bool(ks.converged),'finite':math.isfinite(eh) and math.isfinite(ed),'method_pair':['RHF','PBE']}
```


Ожидаемый численный контракт: `{"hf_converged": true, "pbe_converged": true, "finite": true, "method_pair": ["RHF", "PBE"]}`.


## M12-C3. Сходимость есть, физика диссоциации спорная

Один single-point не доказывает диссоциацию, свободную энергию или барьер.


Рубрика: проверить каждый из трёх пунктов условия по фактическому артефакту. Отдельно оценить происхождение входов, допустимость вывода и независимость переноса. Отсутствие результата — NOT_RUN; отсутствие необходимой среды/реализации — BLOCKED.
