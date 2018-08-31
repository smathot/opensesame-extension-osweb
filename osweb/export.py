# coding=utf-8

"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import hashlib
import time
import json
import base64
import warnings
import tempfile
import zipfile
import json

from bs4 import BeautifulSoup

# Folder containing osweb javascript
js_folder = os.path.join(os.path.dirname(__file__), u'src', u'js')

# Folder containing HTML templates
tmpl_folder = os.path.join(os.path.dirname(__file__), u'src', u'html')


def standalone(osexp, dst, subject=0, fullscreen=False):
    params = {'subject': subject, 'fullscreen': fullscreen}
    mode = u'standalone'
    _html(osexp, dst, mode, _js_files(mode), params, bundled=True)

def jatos(
    osexp,
    dst,
    title='My OpenSesame experiment',
    description='No description',
    subject=0,
    fullscreen=False
):

    mode = u'jatos'
    asset = _unique_hash()
    dirname = tempfile.mkdtemp(suffix=u'.jatos')
    os.mkdir(os.path.join(dirname, asset))
    asset_path = os.path.join(dirname, asset, u'index.html')
    jas_path = os.path.join(dirname, u'info.jas')

    js_sources = _js_files(mode)

    params = {'subject': subject, 'fullscreen': fullscreen}

    _html(
        osexp,
        asset_path,
        mode,
        js_sources,
        params
    )

    info = {
    	'version': '3',
    	'data': {
    		'title': title,
    		'description': description,
    		'groupStudy': False,
    		'dirName': asset,
    		'comments': '',
    		'jsonData': None,
    		'componentList': [{
    			'title': 'Experiment',
    			'htmlFilePath': 'index.html',
    			'reloadable': False,
    			'active': True,
    			'jsonData': None
    		}],
    		'batchList': []
    	}
    }

    with open(jas_path, u'w') as fd:
        json.dump(info, fd)

    with zipfile.ZipFile(dst, 'w') as fd:
        fd.write(jas_path, u'info.jas')
        fd.write(asset_path, os.path.join(asset, u'index.html'))
        for js in js_sources:
            fd.write(js['src'], os.path.join(asset, js['dest']))


# Private functions

def _js_files(mode):

    # The osweb source and vendor js bundles.
    jsFiles = [
        {'src': os.path.join(js_folder, basename), 'dest': os.path.join('js', basename)}
        for basename in os.listdir(js_folder)
        if basename.startswith(u'osweb') or basename.startswith(u'vendors~osweb.')
    ]

    #  The current environment js (Jatos or otherwise)
    envJs = u'{}.js'.format(mode)
    jsFiles.append({'src': os.path.join(js_folder, envJs), 'dest': os.path.join('js', envJs)})
    return jsFiles

def _html(osexp, dst, type_, js=None, params=None, bundled=False):
    # js = js_osweb + [os.path.join(js_folder, u'{}.js'.format(type_))]
    js = js or []
    tmpl = os.path.join(tmpl_folder, u'{}.html'.format(type_))

    # The HTML file parsed as a DOM Tree
    with open(tmpl, 'r') as t_pid:
        dom = BeautifulSoup(t_pid, 'html.parser')

    if bundled:
        scriptTag = dom.new_tag('script', type="text/javascript")
        if params:
            # Embed the params as JSON
            scriptTag.append('const params = JSON.parse(\'{}\')'.format(json.dumps(params)))
        for js_file in js:
            scriptTag.append(_read(js_file))
        dom.head.append(scriptTag)
    else:
        # If a json params file has been specified, save it as a node
        if params:
            # Create a script node that references the JSON file
            scriptTag = dom.new_tag('script', id="parameters", type="text/javascript")
            scriptTag.append('const params = JSON.parse(\'{}\')'.format(json.dumps(params)))
            dom.head.append(scriptTag)
        for js_file in js:
            scriptTag = dom.new_tag('script', src=js_file['dest'], type="text/javascript")
            dom.head.append(scriptTag)

    expTag = dom.new_tag(
        'embed',
        id='osexp_src',
        src='data:application/gzip;base64,' + _read_b64(osexp),
        style='display:none'
    )
    dom.body.append(expTag)

    with open(dst, 'w') as fd:
        fd.write(dom.prettify())


def _read(path):

    with open(path) as fd:
        return fd.read()


def _read_b64(path):

    with open(path, 'rb') as fd:
        e = base64.b64encode(fd.read())
        return e.decode()

def _unique_hash():

    return hashlib.md5(str(time.time()).encode()).hexdigest()

if __name__ == "__main__":
    jatos('','output.zip')

