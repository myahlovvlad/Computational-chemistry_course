"""Создать переносимый снимок учитываемых Git материалов; без сред и личных работ."""
import argparse,hashlib,json,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve()
    if out.exists():raise FileExistsError('Не перезаписываем существующий снимок: '+str(out))
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf-8').split('\0')
    names=sorted(set(n for n in names if n and (ROOT/n).is_file()))
    forbidden={'Books','.venv-base','.venv-chem','.venv-quantum','.git','workspace','cache','converted','tmp','output'}
    manifest={};out.parent.mkdir(parents=True,exist_ok=True)
    with tarfile.open(out,'w:gz') as archive:
      for name in names:
        relative=Path(name)
        if any(part in forbidden or part.startswith('.venv') for part in relative.parts):continue
        source=(ROOT/relative).resolve();source.relative_to(ROOT)
        if source.is_symlink():raise ValueError('Символическая ссылка требует отдельной проверки: '+name)
        manifest[name]=hashlib.sha256(source.read_bytes()).hexdigest()
        archive.add(source,arcname=relative.as_posix(),recursive=False)
    out.with_suffix('.json').write_text(json.dumps({'files_sha256':manifest,'archive_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Snapshot files:',len(manifest),'archive:',out)

if __name__=='__main__':main()
