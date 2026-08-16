python -c "from safe.trainer.cli import main; main()" \
    --config <configファイルのパス> \
    --tokenizer <tokenizerのパス> \
    --dataset <datasetのパス> \
    --output_dir <出力先ディレクトリ> \
    --do_train True \
    --num_labels 9 \
    --torch_compile True \
    --optim "adamw_torch" \
    --learning_rate 1e-5 \
    --prop_loss_coeff 1e-3 \
    --gradient_accumulation_steps 1 \
    --max_steps 5

python -m safe.trainer.cli --help