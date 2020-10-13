import os
path = os.path.abspath('.')

def transform(file_path):
    haveComment = True
    with open(file_path, 'r') as f:
        lines = f.readlines()
        if not len(lines):
            return
        line = lines[0].rstrip('\n')
        comment = '# -*- coding: utf-8'
        if line != comment:
            lines.insert(0, comment+'\n')
            haveComment = False
    if haveComment:
        return
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)




def main(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file == 'add_comment.py':
                continue
            suffix = os.path.splitext(file)[-1]
            if suffix == '.py':
                transform(os.path.join(root, file))
main(path)
