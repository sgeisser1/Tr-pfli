"""Stapel-Rendering ohne Oberfläche (reproduzierbar):
    blender -b --factory-startup --python renders/gen/batch_render.py -- p1 p2 p3 p4 family gateway
Optionen: --samples N (Standard 256)
"""
import sys
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['p1', 'p2', 'p3', 'p4', 'family', 'gateway']
samples = 256
if '--samples' in argv:
    i = argv.index('--samples'); samples = int(argv[i + 1]); del argv[i:i + 2]
exec(open('/home/sgeisser/git/Tr-pfli/renders/gen/render_phase3.py').read())
import time
for job in argv:
    t = time.time()
    key, _, shot = job.partition(':')          # z. B. p2:rueck rendert nur eine Ansicht neu
    if key in HEADS:
        build_design(key, samples=samples)
        print('fertig', render_design(key, (shot,) if shot else ('topf', 'nah', 'rueck')), flush=True)
    elif job == 'family':
        build_family(samples=samples); print('fertig', render_family(), flush=True)
    elif job == 'gateway':
        build_gateway(samples=samples); print('fertig', render_gateway(), flush=True)
    print(job, 'Zeit %.0f s' % (time.time() - t), flush=True)
