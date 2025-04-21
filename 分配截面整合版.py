# -*- coding: utf-8 -*-
from abaqus import *
from abaqusConstants import *
import part
import regionToolset
import codecs

# ———— 模型初始化 ————
modelName = 'Cusinter'
if modelName in mdb.models.keys():
    del mdb.models[modelName]
myModel = mdb.Model(name=modelName)

# ———— 草图与分割 ————
mySketch = myModel.ConstrainedSketch(name='sketch', sheetSize=200.0)
mySketch.rectangle(point1=(0.0, 0.0), point2=(20.0, 20.0))
myPart = myModel.Part(name='Part-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
myPart.BaseShell(sketch=mySketch)

# 添加 100×100 分割线
for i in range(1, 100):
    y = 20.0 * i / 100
    mySketch.Line(point1=(0.0, y), point2=(20.0, y))
for j in range(1, 100):
    x = 20.0 * j / 100
    mySketch.Line(point1=(x, 0.0), point2=(x, 20.0))
faces = myPart.faces.findAt((10.0, 10.0, 0.0), )
myPart.PartitionFaceBySketch(faces=faces, sketch=mySketch)

# ———— 材料与截面定义 ————
model = mdb.models[modelName]
model.Material(name='SinteredCu')
model.materials['SinteredCu'].Elastic(table=((70000.0, 0.34), ))
model.HomogeneousSolidSection(name='Section-Cu', material='SinteredCu', thickness=1.0)
model.Material(name='Pore')
model.materials['Pore'].Elastic(table=((1e-3, 0.0), ))
model.HomogeneousSolidSection(name='Section-Pore', material='Pore', thickness=1.0)

# ———— 读取二值图并记录坐标 ————
file_path = 'porosity.txt'
with codecs.open(file_path, 'r', 'utf-8') as f:
    lines = [line.strip() for line in f]
if len(lines) != 100 or any(len(line) != 100 for line in lines):
    raise ValueError("porosity.txt 必须是 100 行，每行 100 个 ‘0/1’ 字符")
coords_cu = []
coords_pore = []
for l, line in enumerate(lines):
    row = 100 - l
    y_center = (2 * row - 1) / 10.0
    for c, ch in enumerate(line):
        col = c + 1
        x_center = (2 * col - 1) / 10.0
        try:
            fa = myPart.faces.findAt(((x_center, y_center, 0.0),))
            if not fa: continue
        except:
            continue
        if ch == '1': coords_cu.append((x_center, y_center, 0.0))
        else: coords_pore.append((x_center, y_center, 0.0))

# ———— Section 指派 ————
if coords_cu:
    locs_cu = [ (coord,) for coord in coords_cu ]
    fa_cu = myPart.faces.findAt(*locs_cu)
    region_cu = regionToolset.Region(faces=fa_cu)
    myPart.SectionAssignment(region=region_cu, sectionName='Section-Cu',
                             offset=0.0, offsetType=MIDDLE_SURFACE,
                             offsetField='', thicknessAssignment=FROM_SECTION)
    myPart.Set(name='Set-Cu', faces=fa_cu)
    print("✅ Section-Cu 指派完成，面数：%d" % len(fa_cu))
else:
    print("⚠ 未发现任何 Cu 区域，未做 Section-Cu 指派")
if coords_pore:
    locs_pore = [ (coord,) for coord in coords_pore ]
    fa_pore = myPart.faces.findAt(*locs_pore)
    region_pore = regionToolset.Region(faces=fa_pore)
    myPart.SectionAssignment(region=region_pore, sectionName='Section-Pore',
                             offset=0.0, offsetType=MIDDLE_SURFACE,
                             offsetField='', thicknessAssignment=FROM_SECTION)
    myPart.Set(name='Set-Pore', faces=fa_pore)
    print("✅ Section-Pore 指派完成，面数：%d" % len(fa_pore))
else:
    print("⚠ 未发现任何 Pore 区域，未做 Section-Pore 指派")

# ———— 装配与边界条件 ————
assembly = model.rootAssembly
assembly.DatumCsysByDefault(CARTESIAN)
inst = assembly.Instance(name='Part-1-1', part=myPart, dependent=ON)

# 底边所有小边集合
bottom_edge_points = [(((2*c-1)/10.0, 0.0, 0.0),) for c in range(1, 101)]
edges_bot = inst.edges.findAt(*bottom_edge_points)
assembly.Set(name='Set-Bottom', edges=edges_bot)
# 顶边所有小边集合
top_edge_points = [(((2*c-1)/10.0, 20.0, 0.0),) for c in range(1, 101)]
edges_top = inst.edges.findAt(*top_edge_points)
assembly.Set(name='Set-Top', edges=edges_top)

# 创建载荷步
model.StaticStep(name='Load', previous='Initial', timePeriod=1.0,
                 initialInc=0.1, minInc=1e-5, maxInc=0.1)
# 底边完全固定
model.DisplacementBC(name='BC-Bottom', createStepName='Initial',
                     region=assembly.sets['Set-Bottom'], u1=0.0, u2=0.0, ur3=0.0)
# 顶边 20um 水平位移，线性加载
model.TabularAmplitude(name='amp1', timeSpan=STEP,
                       data=((0.0, 0.0), (1.0, 20.0)))
model.DisplacementBC(name='BC-Top', createStepName='Load',
                     region=assembly.sets['Set-Top'], u1=20.0, u2=UNSET,
                     amplitude='amp1')

print('🎉 模型划分、Section 指派及边界条件完成。')

