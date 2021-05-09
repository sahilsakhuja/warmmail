import os

from csci_utils.canvas import CanvasManager

canvas_mgr = CanvasManager(os.environ.get("CANVAS_COURSE"))
canvas_mgr.csci_utils_updated = False
canvas_mgr.cookiecutter_updated = False
canvas_mgr.addl_comments = (
    "Sphinx documentation link: https://warmmail.readthedocs.io/en/latest/"
)
comments = canvas_mgr.pset_submit_assignment(
    "Final Project", working_dir="2021sp-final-project-sahilsakhuja"
)
print("Assignment submitted with comments:")
print(comments)
