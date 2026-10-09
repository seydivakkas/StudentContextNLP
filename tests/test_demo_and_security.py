import pandas as pd
from pathlib import Path
from audit_dataset import SPLITS, audit, read_split
from scripts.create_synthetic_fixture import build
from train_lexical import prepare, input_text


def test_demo_files_and_unseen_questions(tmp_path):
    build(tmp_path, repeats=2)
    frames, paths = {}, {}
    for s in SPLITS:
        frames[s], paths[s] = read_split(tmp_path, s)
    result = audit(frames, paths)
    assert not result['fatal_errors']
    assert result['cross_split']['test_uq']['question_overlap_with_train'] == 0
    assert (tmp_path/'SYNTHETIC_DEMO.json').exists()


def test_never_use_reference_or_label_as_feature():
    a = pd.DataFrame([{'id':'x','question':'How do cells divide?',
        'student_answer':'Cells split over time', 'reference_answer':'REFERENCE_A', 'label':0}])
    b = a.copy(); b['reference_answer']='REFERENCE_B'; b['label']=1
    aa, bb = prepare(a), prepare(b)
    for cond in ['B0','B1','B2','B3']:
        assert input_text(aa,cond) == input_text(bb,cond)
