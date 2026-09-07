#!/usr/bin/env Rscript

# Test Qwen ST effects in ten ERP windows with by-subject and by-item intercepts.
suppressPackageStartupMessages(library(readxl))
suppressPackageStartupMessages(library(writexl))
suppressPackageStartupMessages(library(lme4))
suppressPackageStartupMessages(library(lmerTest))

script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_dir <- dirname(normalizePath(sub("^--file=", "", script_arg[[1]]), mustWork = FALSE))
repo_root <- normalizePath(file.path(script_dir, ".."), mustWork = FALSE)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 3) stop("usage: Rscript s1_erp_time_window_lme.R [ITEM_LIST.xlsx] [DATA.xlsx] [OUTPUT_DIR]")
item_path <- if (length(args) >= 1) args[[1]] else file.path(repo_root, "data", "input", "erp_item_list.xlsx")
data_path <- if (length(args) >= 2) args[[2]] else file.path(repo_root, "data", "input", "erp_data_analysis.xlsx")
output_dir <- if (length(args) >= 3) args[[3]] else file.path(repo_root, "results")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

items <- as.data.frame(read_excel(item_path, sheet = "word"))
required_items <- c("Item", "ST_C1_qwen", "ST_C2_qwen")
if (length(setdiff(required_items, names(items)))) stop("item list lacks Qwen ST columns")
items$ST_C1_qwen <- as.numeric(scale(items$ST_C1_qwen))
items$ST_C2_qwen <- as.numeric(scale(items$ST_C2_qwen))

erp <- if (grepl("\\.csv$", data_path, ignore.case = TRUE)) {
  read.csv(data_path, check.names = FALSE)
} else {
  as.data.frame(read_excel(data_path))
}
erp <- merge(erp, items[required_items], by = "Item", all.x = FALSE, all.y = FALSE)
erp <- erp[complete.cases(erp[, c("ST_C1_qwen", "ST_C2_qwen")]), ]
if (nrow(erp) != 311202) warning(sprintf("expected 311,202 observations, found %s", nrow(erp)))

windows <- paste0("TW", 1:10)
milliseconds <- c("0-100", "100-200", "200-300", "300-400", "400-500", "500-600", "600-700", "700-800", "800-900", "900-1000")
formula_text <- "y ~ Dum_HE + Dum_AN1 + Dum_AN2 + S_W + LogCD_W + LogCD_C1 + LogCD_C2 + LogNOH_C1 + LogNOH_C2 + ST_C1_qwen + ST_C2_qwen + (1|Subject) + (1|Item)"
rows <- list()
for (index in seq_along(windows)) {
  window <- windows[[index]]
  erp$y <- erp[[window]]
  fit <- tryCatch(lmer(as.formula(formula_text), data = erp, REML = TRUE), error = function(e) NULL)
  converged <- !is.null(fit) && is.null(fit@optinfo$conv$lme4$messages)
  row <- data.frame(TW = window, ms = milliseconds[[index]], converged = converged)
  for (term in c("ST_C1_qwen", "ST_C2_qwen")) {
    prefix <- if (term == "ST_C1_qwen") "ST_C1_qwen" else "ST_C2_qwen"
    if (is.null(fit)) {
      row[[paste0(prefix, "_coef")]] <- NA_real_
      row[[paste0(prefix, "_se")]] <- NA_real_
      row[[paste0(prefix, "_p")]] <- NA_real_
    } else {
      coefs <- coef(summary(fit))
      row[[paste0(prefix, "_coef")]] <- coefs[term, "Estimate"]
      row[[paste0(prefix, "_se")]] <- coefs[term, "Std. Error"]
      row[[paste0(prefix, "_p")]] <- coefs[term, "Pr(>|t|)"]
    }
  }
  rows[[index]] <- row
}
result <- do.call(rbind, rows)
result$ST_C1_qwen_p_fdr <- p.adjust(result$ST_C1_qwen_p, method = "BH")
result$ST_C2_qwen_p_fdr <- p.adjust(result$ST_C2_qwen_p, method = "BH")
result$ST_C1_qwen_sig <- result$ST_C1_qwen_p_fdr < .05
result$ST_C2_qwen_sig <- result$ST_C2_qwen_p_fdr < .05
write_xlsx(result, file.path(output_dir, "erp_time_window_results.xlsx"))

human_c1 <- c("TW1", "TW7", "TW8")
human_c2 <- c("TW2", "TW4", "TW7")
qwen_c1 <- result$TW[result$ST_C1_qwen_sig]
qwen_c2 <- result$TW[result$ST_C2_qwen_sig]
overlap <- data.frame(
  position = c("C1", "C2"),
  human_significant_windows = c(paste(human_c1, collapse = ";"), paste(human_c2, collapse = ";")),
  qwen_significant_windows = c(paste(qwen_c1, collapse = ";"), paste(qwen_c2, collapse = ";")),
  overlapping_windows = c(paste(intersect(human_c1, qwen_c1), collapse = ";"), paste(intersect(human_c2, qwen_c2), collapse = ";"))
)
write_xlsx(overlap, file.path(output_dir, "erp_window_overlap.xlsx"))
print(result, digits = 6)
