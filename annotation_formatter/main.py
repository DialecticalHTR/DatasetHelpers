from environs import env
env.read_env()

import argparse
from pathlib import Path
from typing import List

from s3 import *
from annotations import *
from exporter import *
from builder import *


def main():
    # 0. Create parser
    parser = argparse.ArgumentParser(
        prog='to_trocr',
        description='Converts Label Studio annotations to a dataset'
    )
    parser.add_argument("--from", nargs=2, metavar=("TYPE", "VALUE"), action='append')
    parser.add_argument('--to', nargs=2, metavar=("TYPE", "VALUE"), action='append')
    parser.add_argument('--data', choices=['trocr'], default='trocr')
    args = parser.parse_args()

    # 1. Connect to S3
    s3_connection = S3ConnectionConfig(
        region=env('AWS_REGION_NAME'),
        endpoint=env('AWS_ENDPOINT_URL')
    )
    s3_credentials = S3Credentials(
        access_key_id=env('AWS_ACCESS_KEY_ID'),
        secret_access_key=env('AWS_SECRET_ACCESS_KEY'),
        session_token=env('AWS_SESSION_TOKEN')
    )
    s3_context = S3Context(s3_connection, s3_credentials)

    # 2. Get task annotations
    tasks: List[Task] = []
    for loader in (_from := getattr(args, 'from')):
        match loader:
            case ['s3', s3_url]:
                loader_tasks = S3AnnotationLoader(s3_context).get_tasks(s3_url)
            case ['export', json_filepath]:
                loader_tasks = ExportAnnotationLoader().get_tasks(json_filepath)
            case _:
                raise ValueError(f'Unknown data source {_from[0]}')
        tasks.extend(loader_tasks)
    
    # 3. Prepare exporters
    exporters: List[Exporter] = []
    for output in (to := args.to):
        match output:
            case ['s3', s3_url]:
                exporter = S3Exporter(s3_context, s3_url)
            case ['folder', path]:
                exporter = FolderExporter(Path(path))
            case _:
                raise ValueError(f'Unknown data output {to[0]}')
        exporters.append(exporter)

    # 4. Pick an dataset builder and build
    match args.data:
        case 'trocr':
            builder = TrOCRBuilder(s3_context)
        case _:
            raise ValueError(f'Unknown dataset type {args.data}')
    
    builder.build_dataset(tasks, exporters)


if __name__ == '__main__':
    main()
