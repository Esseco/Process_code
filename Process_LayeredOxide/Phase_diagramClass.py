import numpy as np
import pandas as pd
from pymatgen.core import Composition
from scipy.spatial import ConvexHull


class LayerOxidePhaseDiagram:

    def __init__(
        self,
        parse_composition=True,
        na_col='Na_content',
        com_col='Composition',
        energy_col='energy',
        formula_e_col='formula_e',
        formation_e_col='formation_e',
        need_phase=False,
        phase_col='phase',
        calc_ehull=False,
        start_na=0.0,
        end_na=1.0,
        atol=1e-2,
    ):
        self.parse_composition = parse_composition
        self.na_col = na_col
        self.energy_col = energy_col
        self.formula_e_col = formula_e_col
        self.formation_e_col = formation_e_col
        self.need_phase = need_phase
        self.phase_col = phase_col
        self.composition = com_col
        self.calc_ehull = calc_ehull
        self.start_na = start_na
        self.end_na = end_na
        self.atol = atol

    @staticmethod
    def composition_to_na(self):
        try:
            comp = Composition(self.composition)
            return 2 * comp.get('Na', 0) / comp['O']
        except Exception:
            return np.nan

    def identify_phase(self, df):
        """识别相结构类型"""
        t = pd.to_numeric(df['T:6'], errors='coerce').fillna(0)
        o = pd.to_numeric(df['O:6'], errors='coerce').fillna(0)
        df[self.phase_col] = np.select(
            [(t > 0) & (o > 0), (t > 0), (o > 0)],
            ['OP2', 'P3', 'O3'],
            default='O1'
        )
        return df

    def process(self, df):
        """主处理流程"""
        df = df.copy()

        # 相识别
        if self.need_phase:
            self.identify_phase(df)

        # Na含量提取
        if self.parse_composition:
            df['Na_content'] = df['composition'].map(self.composition_to_na)
        else:
            df['Na_content'] = pd.to_numeric(df[self.na_col], errors='coerce')

        # 能量转换：eV/atom → eV/NaxTMO2
        energy = pd.to_numeric(df[self.energy_col], errors='coerce')
        df[self.formula_e_col] = energy * (df['Na_content'] + 3)

        # 形成能计算
        x = df['Na_content']
        e = df[self.formula_e_col]

        e0 = e[np.isclose(x, self.start_na, atol=self.atol)].min()
        e1 = e[np.isclose(x, self.end_na, atol=self.atol)].min()

        if pd.isna(e0) or pd.isna(e1):
            df[self.formation_e_col] = np.nan
            return df

        ref = e0 + (x - self.start_na) * (e1 - e0) / (self.end_na - self.start_na)
        df[self.formation_e_col] = (e - ref) * 1000  # meV / NaxTMO2

        # 凸包能计算（可选）
        if self.calc_ehull:
            df['energy_above_hull'] = self._calculate_energy_above_hull(df, x)

        return df

    def _calculate_energy_above_hull(self, df, x):
        """基于formation_e构建下凸包，计算能量高于凸包的值"""
        formation_e = df[self.formation_e_col].values
        x_values = x.values
        
        # 过滤有效数据
        valid_mask = ~(np.isnan(formation_e) | np.isnan(x_values))
        if valid_mask.sum() < 2:
            return np.full_like(formation_e, np.nan)
        
        try:
            # 构建凸包
            points = np.column_stack((x_values[valid_mask], formation_e[valid_mask]))
            hull = ConvexHull(points)
            
            # 计算每点到凸包的能量高度
            ehull_values = []
            valid_indices = np.where(valid_mask)[0]
            
            for x_val, e_val in zip(x_values[valid_mask], formation_e[valid_mask]):
                # 遍历凸包的每条边，找到包含此x的线段
                min_dist = 0
                for simplex in hull.simplices:
                    p1, p2 = points[simplex[0]], points[simplex[1]]
                    x1, e1 = p1
                    x2, e2 = p2
                    
                    # 检查x是否在线段范围内
                    x_min, x_max = min(x1, x2), max(x1, x2)
                    if x_min - 1e-10 <= x_val <= x_max + 1e-10:
                        # 线性插值得到凸包上的能量
                        if abs(x2 - x1) > 1e-10:
                            e_on_hull = e1 + (x_val - x1) * (e2 - e1) / (x2 - x1)
                        else:
                            e_on_hull = (e1 + e2) / 2
                        
                        min_dist = max(min_dist, e_val - e_on_hull)
                
                ehull_values.append(max(0, min_dist))
            
            # 构建完整结果数组
            energy_above_hull = np.full_like(formation_e, np.nan, dtype=float)
            energy_above_hull[valid_indices] = np.array(ehull_values)
            
            # 归一化：除以 (Na_content + 3)
            result = energy_above_hull / (df['Na_content'].values + 3)
            return result
            
        except Exception as e:
            print(f"凸包计算异常: {e}")
            return np.full_like(formation_e, np.nan)