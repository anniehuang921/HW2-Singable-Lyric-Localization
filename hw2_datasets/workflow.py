"""One-song Phase4B orchestration, reusing existing translation/singing modules."""
from hw2_translation.controller import Controller
from hw2_singing.adapter import SingingController
RID='CSD_en042a'
class ExcerptController(Controller):
    def load_saved(self,demo_id):
        record=super().load_saved(demo_id)
        if demo_id==RID and record.get('source_revision')!=self.presenter.demos[demo_id].source_revision:raise ValueError('保存比較不屬於目前核對片段版本')
        return record

    def translate(self,demo_id,progress=lambda message:None):
        if demo_id!=RID or not getattr(self.presenter,'excerpt',None):raise ValueError('本輪僅授權已核對 CSD_en042a 片段翻譯')
        try:return self.load_saved(demo_id)
        except ValueError:return super().translate(demo_id,progress)

class ExcerptSinger(SingingController):
    def generate(self,demo_id,comparison,candidate,edited='',before=None,settings=None):
        if demo_id==RID and candidate in ('direct','blt_assisted'):
            try:return self.load_saved(demo_id,comparison,candidate,edited,before,settings)
            except ValueError:pass
        return super().generate(demo_id,comparison,candidate,edited,before,settings)

def presenter():
    from hw2_ui.catalog import read_catalog,DEFAULT_ROOT
    from .csd import CSD
    from .presenter import DatasetPresenter
    from .excerpt import load
    p=DatasetPresenter(read_catalog(),{'yingmusic_official':DEFAULT_ROOT},CSD());p.enable_excerpt(load());return p
