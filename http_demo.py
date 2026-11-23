"""Run the HTTP demo from a downloaded repository without machine-specific paths."""
import argparse
import hashlib
from pathlib import Path
import runpy
import secrets
import sys
from zipfile import ZipFile


ROOT=Path(__file__).resolve().parent
SOURCE_SHA256='d4472a07971e78124b05eb51c5626cff2fa76592dcf459f3dc68cfb7187dc36a'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--interactive',action='store_true',help='Pause at the original and mutant services for Swagger inspection')
    p.add_argument('--prepare-only',action='store_true',help='Extract source and generate local demo settings; do not start services')
    p.add_argument('--build-images',action='store_true',help='Build/pull missing Docker images; needs Internet and may take several minutes')
    args=p.parse_args()
    archive=ROOT/'http-demo-source.zip'
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest()!=SOURCE_SHA256:
        p.exit(1,'HTTP source archive is missing or its checksum differs. Download the complete repository again.\n')
    target=ROOT/('.http-demo-'+SOURCE_SHA256[:8])
    if not (target/'.prepared').is_file():
        target.mkdir(exist_ok=True)
        with ZipFile(archive) as z:
            for entry in z.infolist():
                if not (target/entry.filename).resolve().is_relative_to(target.resolve()):
                    p.exit(1,'Invalid archive path.\n')
            z.extractall(target)
        template=target/'work/RESTestBench/services/fastapi/original/.env.example'
        env=template.with_name('.env')
        values={'DEMO_SECRET_KEY':secrets.token_urlsafe(32),'DEMO_DB_PASSWORD':secrets.token_urlsafe(24),
                'DEMO_ADMIN_PASSWORD':secrets.token_urlsafe(24)}
        content=template.read_text(encoding='utf-8')
        for key,value in values.items():
            content=content.replace('{'+key+'}',value)
        env.write_text(content,encoding='utf-8')
        (target/'.prepared').write_text(SOURCE_SHA256+'\n',encoding='utf-8')
    if args.prepare_only:
        print('Prepared local HTTP sources:',target)
        print('No container, model generation, or HTTP request was started.')
        return
    launcher=target/'Chay-HTTP-Demo.py'
    sys.argv=[str(launcher)]
    if args.interactive:sys.argv.append('--interactive')
    if args.build_images:sys.argv.append('--build-images')
    runpy.run_path(str(launcher),run_name='__main__')


if __name__=='__main__':
    main()
