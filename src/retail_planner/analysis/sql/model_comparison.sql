-- Selection is based on validation, even if a different model looks better on holdout.
SELECT method, selected, validation_wrmsse, holdout_wrmsse, holdout_wape,
       DENSE_RANK() OVER (ORDER BY validation_wrmsse) AS validation_rank
FROM model_evaluation
ORDER BY validation_rank, method;
