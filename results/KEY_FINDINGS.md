# Key findings / 关键结果

## Convergent validity / 收敛效度

| Measure | Position | N | Pearson | Spearman |
|---|---:|---:|---:|---:|
| Qwen vs. human | C1 | 8,785 | .4879 | .5910 |
| Qwen vs. human | C2 | 8,785 | .4764 | .5384 |
| Tencent embedding vs. human | C1 | 8,168 | .5302 | .5487 |
| Tencent embedding vs. human | C2 | 8,168 | .4826 | .4973 |

Human-rating split-half Pearson/Spearman correlations are .7258/.6802 for C1 and .7951/.7656 for C2 (N=1,176). Every archived C1CST/C2CST value equals the recalculated item mean.

人工评分 split-half 的 Pearson/Spearman 相关为：C1=.7258/.6802，C2=.7951/.7656（N=1,176）；所有归档均值均与个体评分重算结果一致。

## Behavioral incremental validity / 行为方差增量

After lexical controls and outlier handling, N=8,402. For zRT, adjusted R² is .4193 for the baseline, .4206 with human ST, and .4225 with Qwen ST. For ERR, the corresponding values are .1967, .1999, and .2006. Qwen additions are significant for both outcomes.

控制词汇变量并排除离群值后，样本量为 8,402。zRT 的调整后 R² 依次为基线 .4193、人工 ST .4206、Qwen ST .4225；ERR 依次为 .1967、.1999、.2006。Qwen ST 在两个因变量上的增量均显著。

## ERP windows / ERP 时间窗

All ten archived LME models converged. Qwen C1 is significant after FDR correction in TW3 (200–300 ms), TW7 (600–700 ms), and TW8 (700–800 ms). The overlap with published human C1 windows is TW7 and TW8. Qwen C2 has no FDR-significant window.

十个归档 LME 均收敛。Qwen C1 经 FDR 校正后在 TW3、TW7、TW8 显著，与人工 C1 重叠于 TW7 和 TW8；Qwen C2 无 FDR 显著窗口。

## Lexical structure / 词汇结构

The 12-class human benchmark accuracy is 904/1,015=89.06%. On 8,401 behavioral items, structure raises raw R² from .4199 to .4257 for zRT and from .1974 to .2012 for ERR. The improvements are significant. Adding ST-by-structure interactions does not significantly improve either outcome.

12 类人工评估集准确率为 904/1,015=89.06%。在 8,401 个行为项目上，加入词汇结构后 zRT 的原始 R² 从 .4199 增至 .4257，ERR 从 .1974 增至 .2012，均显著；ST×结构交互均不显著。

