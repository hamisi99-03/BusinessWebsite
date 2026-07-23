from django import forms


class DragDropFileInput(forms.ClearableFileInput):
    template_name = "ecommerce/widgets/drag_drop_file_input.html"

    class Media:
        css = {
            "all": ("ecommerce/widgets/drag_drop.css",)
        }
        js = ("ecommerce/widgets/drag_drop.js",)
