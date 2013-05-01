import os, importlib, markdown, pprint, data
from jinja2 import Environment, FileSystemLoader

# Initialize components for manipulating content before it is written out.
md = markdown.Markdown(
    extensions = ['extra', 'codehilite', 'meta', 'wikilinks'],
    output_format = 'html5'
)
jn = Environment(loader = FileSystemLoader(['.', 'templates']))
jn.globals = dict(jn.globals, **data.data)


def render(template, data):
    template = jn.get_template(template)
    return template.render(**data)


def tyrant(folder):
    """Convert tyrant folders into a static website."""
    tyrant_file = importlib.import_module('content.' + folder)
    target_dir = "/".join(tyrant_file.__path__) + '/data/'

    # Convert Data.
    pages = []
    for page in os.listdir(target_dir):
        if page.endswith('markdown') and os.path.isfile(target_dir + page):
            with open(target_dir + page) as pagedata:
                pages.append({
                    'data': md.convert(pagedata.read()),
                    'meta': md.Meta,
                    'name': page.rsplit('.', 1)[0]
                })

    # Iterate Data and Construct Pages.
    results = []
    [os.mkdir(p) for p in ['static', 'output', 'output/' + folder] if not os.path.isdir(p)]
    for page in pages:
        # This is extremely ugly, fixing this code duplication is the first
        # thing I need to do in the near future.
        if folder != 'index':
            # Create folders for every output file, to get nice looking URL's
            # without any server modifications.
            if not os.path.isdir('output/{}/{}/'.format(folder, page['name'])):
                os.mkdir('output/{}/{}/'.format(folder, page['name']))

            # Generate the index file.
            target_out = 'output/{}/{}/index.html'.format(folder, page['name'])
            results.append((target_out, page))
            with open(target_out, 'w+') as f:
                f.write(render('./content/' + folder + '/view.tmp', page).encode('UTF-8'))
        else:
            if page['name'] == 'index':
                with open('output/index.html', 'w+') as f:
                    f.write(render('./content/' + folder + '/view.tmp', page).encode('UTF-8'))
            else:
                # Create folders for every output file, to get nice looking
                # URL's without any server modifications.
                if not os.path.isdir('output/{}/'.format(page['name'])):
                    os.mkdir('output/{}/'.format(page['name']))

                # Generate the index file.
                target_out = 'output/{}/index.html'.format(page['name'])
                results.append((target_out, page))
                with open(target_out, 'w+') as f:
                    f.write(render('./content/' + folder + '/view.tmp', page).encode('UTF-8'))

    # Link static files in the output.
    if not os.path.exists('output/static'):
        os.symlink('../static', 'output/static')

    # Process receives a list of generated files and their data. This can be
    # used to do postprocessing, creating extra lists etc.
    if 'process' in dir(tyrant_file):
        tyrant_file.process(results)


if __name__ == '__main__':
    # Search for Tyrant folders. Tyrant folders are python modules containing
    # jinja2 templates and markdown files.
    folders = []
    for entry in os.listdir('./content/'):
        # Ignore things that aren't even folders.
        if not os.path.isdir('./content/' + entry):
            continue

        # Tyrant folders _must_ be python modules, which can be detected by
        # checking for a __init__.py file.
        if not os.path.exists('./content/' + entry + '/__init__.py'):
            print('Skipping {} - Not a python module.'.format(entry))
            continue

        # Tyrant folders _must_ contain markdown files, contained in a data
        # folder.
        if not os.path.isdir('./content/' + entry + '/data'):
            print('Skipping {} - No data folder found.'.format(entry))
            continue

        # Tyrant folders _must_ contain a jinja2 templates folder.
        if not os.path.isfile('./content/' + entry + '/view.tmp'):
            print('Skipping {} - No view template found.'.format(entry))
            continue

        folders.append(entry)

    map(tyrant, folders)
