from flask import Flask, send_from_directory, request, render_template, send_file, abort
from tempfile import mkdtemp
import os
from threading import Thread
from glob import glob
import subprocess

app = Flask(__name__)

results = []

class Evaluator(Thread):
  def __init__(self, *args, rid, **kws):
    Thread.__init__(self, *args, **kws)
    self.rid = rid
  
  def run(self):
    dir = results[self.rid]['dir']
    results[self.rid]['successful'] = False
    try:
      subprocess.check_output(['python','/rpg_trajectory_evaluation-0.1/scripts/analyze_trajectory_single.py',dir])
    except subprocess.CalledProcessError as e:
      if b'Done processing error type traj_est' not in e.output:
        return
      results[self.rid]['successful'] = True
      results[self.rid]['pdf'] = list(map(
        lambda x: os.path.relpath(x, dir),
        glob(os.path.join(dir, '**/*.pdf'), recursive=True)
      ))
      results[self.rid]['archive'] = os.path.join(dir, '%d.tar.gz' % self.rid)
      subprocess.call([
        'tar', 'czf',
        results[self.rid]['archive'],
        '-C', dir, 'plots', 'saved_results'
      ])
    finally:
      results[self.rid]['finished'] = True

def valid(file):
  return file and file.filename != ''

@app.route('/', methods=['GET', 'POST'])
def index():
  msg = None
  if request.method == 'POST':
    dir = mkdtemp()
    ground = request.files['ground']
    traj = request.files['traj']
    config = request.files['config']
    if not (valid(ground) and valid(traj) and valid(config)):
      msg = "ERROR: missing file(s)"
      # TODO: remove unused temp dir
    else:
      ground.save(os.path.join(dir, 'stamped_groundtruth.txt'))
      traj.save(os.path.join(dir, 'stamped_traj_estimate.txt'))
      config.save(os.path.join(dir, 'eval_cfg.yaml'))
      rid = len(results)
      results.append({'dir': dir, 'finished': False})
      # TODO: run evaluation
      Evaluator(rid=rid).start()
      msg = 'INFO: view result at <a href="/%d">this page</a>' % rid
  return render_template('index.html', msg=msg)

@app.route('/<int:rid>')
def show_result(rid):
  if rid >= len(results) or not results[rid]['finished']:
    return 'Evaluation not finished. Refresh to update status.'
  else:
    return render_template('show.html', rid=rid, result=results[rid])

@app.route('/download/<int:rid>')
def download(rid):
  if results[rid]['successful']:
    return send_file(results[rid]['archive'])
  else:
    return 'Archive not available!'

@app.route('/<int:rid>/<path:subpath>')
def direct_access_file(rid, subpath):
  filepath = os.path.join(results[rid]['dir'], subpath)
  if not os.path.isfile(filepath): abort(404)
  return send_file(filepath)
