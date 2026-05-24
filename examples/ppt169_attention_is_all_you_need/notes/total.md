# 01_cover

Today we are reading what is probably the single most influential machine learning paper of the last decade: Attention Is All You Need, by Vaswani and seven coauthors at Google Brain, Google Research, and the University of Toronto, presented at NeurIPS 2017. The title is the thesis: drop recurrence and convolution, use only attention, and you get a model that is faster to train, easier to parallelize, and stronger on machine translation than anything that came before. Over the next sixteen slides we'll walk through what the Transformer actually is, how the attention mechanism works, why the authors chose this design, and what the experiments showed.

---

# 02_why_it_matters

Before we get into the architecture, let's see what the paper is actually claiming. On the WMT 2014 English to German translation task, the Transformer big model scored 28.4 BLEU, beating the previous best ensemble by two full points as a single model. On WMT 2014 English to French, it set a new single-model state of the art at 41.8 BLEU. And it did all this by training for three and a half days on eight P100 GPUs — a small fraction of the cost of the strong baselines. The architecture has no recurrence and no convolution; it is built entirely from attention and feed-forward layers. Quality up, cost down, parallelization unlocked.

---

# 03_sequence_evolution

To appreciate the move, it helps to look at where sequence modeling was sitting in 2017. Recurrent networks — RNNs, LSTMs, GRUs — were the default, but they compute step by step and resist parallelization. Convolutional alternatives like ByteNet and ConvS2S could parallelize, but signals between distant positions still had to travel through many layers, growing linearly or logarithmically with distance. Self-attention does something different: every position relates to every other position in one constant-time hop. Visually you can think of it as moving from a chain to a local field to a fully connected mesh — and that mesh is what the Transformer leans into.

---

# 04_rnn_cnn_limits

Let's name the constraints the authors are trying to lift. First, the sequential bottleneck: in any RNN, hidden state at time t depends on hidden state at t minus one, so you cannot parallelize within a single training example. Second, long-range path length: distant tokens have to be related through many intermediate operations, which makes learning long-range dependencies hard. Third, memory ceiling: long sequences eat GPU memory, capping batch size and throughput. The Transformer attacks all three at once by replacing the entire backbone with attention.

---

# 05_architecture_overview

This is figure one from the paper — the Transformer architecture. Read it from the bottom up. Inputs and outputs both come in as embeddings, with a sinusoidal positional encoding added. The encoder on the left is a stack of six identical layers; each layer has multi-head self-attention followed by a position-wise feed-forward network, with Add and Norm wrapping each sub-layer. The decoder on the right is also six layers, but inserts a third sub-layer that attends back to the encoder output, and its self-attention is masked so it cannot peek at future tokens. The whole thing ends with a linear projection and softmax to produce token probabilities. The skeleton is the same as prior seq2seq models — what is new is what fills the boxes.

---

# 06_encoder_decoder

Let's compare the encoder and decoder side by side. The encoder has two sub-layers per block: multi-head self-attention, then a position-wise feed-forward network. The decoder has three: masked multi-head self-attention, then encoder-decoder attention, then the feed-forward network. Around every sub-layer the same wrapper applies — output equals LayerNorm of x plus Sublayer of x, the classic residual connection plus normalization. All sub-layers and embeddings emit a 512-dimensional vector so the residual addition is well-defined. The three asymmetries on the decoder side are the third sub-layer, the causal mask that preserves auto-regression, and the one-position shift of the output embeddings.

---

# 07_scaled_dot_product

Here is the heart of the model — scaled dot-product attention. You start with three matrices: queries Q, keys K, and values V. You compute the dot product of every query with every key, scale by the square root of the key dimension, apply a row-wise softmax to get attention weights, and then multiply by V to produce the output. The scaling factor matters. For large key dimensions the dot products grow in magnitude, pushing the softmax into regions with vanishingly small gradients. Dividing by root d sub k counteracts that. Once you have the weights, the output is just a weighted average of the value vectors — that's all attention is.

---

# 08_multi_head_attention

Multi-head attention is the next move. Instead of running one attention function over the full 512-dimensional vectors, the authors split into h equals eight independent heads, each operating on 64-dimensional projections of Q, K, and V. The projections are learned, so each head can specialize on a different kind of relationship. The heads run in parallel, their outputs are concatenated, and a final linear projection maps back to 512. The total compute is roughly the same as a single full-dimensional head, but the model gains the ability to attend to different representation subspaces at different positions simultaneously.

---

# 09_three_uses

The same attention mechanism shows up in three places in the Transformer, with three slightly different roles. In encoder self-attention, queries, keys, and values all come from the previous encoder layer; every source position attends to every other. In decoder masked self-attention, the same setup applies, but illegal future positions are set to minus infinity before the softmax, so position i attends only to positions less than or equal to i — that's how auto-regression is preserved. In encoder-decoder attention, queries come from the decoder while keys and values come from the encoder output, letting every decoder position retrieve relevant information from anywhere in the source sequence. One mechanism, three roles.

---

# 10_ffn_residual_layernorm

The supporting cast inside every layer is just three small ideas. The position-wise feed-forward network is two linear layers with a ReLU between, applied identically at every position, with an inner dimension of 2048. The residual connection adds the sub-layer's input back to its output, which keeps the gradient signal flowing through deep stacks. Layer normalization then standardizes across the feature dimension. Put them together and the output of every sub-layer is LayerNorm of x plus Sublayer of x. Nothing here is novel by itself — but composing them around attention is what makes the architecture trainable at depth.

---

# 11_positional_encoding

Because there is no recurrence and no convolution, the model has no built-in notion of token order. The authors recover order with a deterministic sinusoidal positional encoding added to each input embedding. Even dimensions use a sine wave, odd dimensions use a cosine wave, and the wavelengths form a geometric progression from two pi up to ten thousand times two pi. The neat property is that for any fixed offset k, the encoding at position pos plus k is a linear function of the encoding at pos — so the model can easily learn to attend by relative position via a simple linear combination. Order is injected, not learned.

---

# 12_complexity_table

This is table one from the paper, and it is the strongest argument for self-attention. A self-attention layer pays O of n squared times d in compute, but in exchange every pair of positions is exactly one operation apart. A recurrent layer pays O of n times d squared, but it takes O of n sequential operations and the maximum path length between two positions is O of n. Convolutional layers fall in between. For typical NLP workloads where the sequence length is shorter than the representation dimension, self-attention is actually faster than recurrence — and the constant path length makes long-range dependencies far easier to learn.

---

# 13_training_setup

A quick word on how this was trained. The base model trains in twelve hours on eight P100 GPUs in one machine; the big model trains in three and a half days on the same hardware. Batches were grouped by similar sequence length to keep about twenty-five thousand source and twenty-five thousand target tokens per batch. The optimizer is Adam with beta two pushed up to 0.98, and a custom learning rate schedule that warms up linearly for four thousand steps then decays as one over the square root of the step count. Regularization is dropout at 0.1 applied to every sub-layer output and to the sum of embedding and positional encoding, plus label smoothing of 0.1.

---

# 14_results

Here are the headline results — table two from the paper. The Transformer big scores 28.4 BLEU on English to German, beating the previous best ensemble by two full BLEU points as a single model. On English to French it scores 41.8, a new single-model state of the art. And it does all this with about 2.3 times 10 to the 19 training floating-point operations, which is well below most strong baselines. The base model alone, trained in twelve hours, already beats almost every prior published model. The combination of better quality and lower training cost is what made this paper land so hard.

---

# 15_ablations

The variation study in table three gives us five takeaways worth remembering. First, head count has a sweet spot: a single head loses about 0.9 BLEU compared to eight heads, but going to thirty-two also degrades. Second, the key dimension matters more than the value dimension — determining compatibility is the harder learning problem. Third, scaling up the model dimension and the depth consistently improves quality, so the architecture scales monotonically with capacity. Fourth, dropout is essential — removing it loses roughly half a BLEU to a full BLEU point even at p equals 0.1. Fifth, label smoothing slightly hurts perplexity but improves BLEU, which is a reminder to optimize for the metric you actually ship on.

---

# 16_conclusion

To close — this 2017 paper turned out to be one of the most consequential architectural ideas in modern machine learning. The Transformer became the substrate for BERT, for GPT, for T5, for the Vision Transformer, for AlphaFold, for CLIP, for almost every large language model in production today, including the one talking to you right now. The core insight — that just attention, with no recurrence and no convolution, is the right inductive bias for sequence modeling — turned out to generalize far beyond translation, to almost every modality we work with. One paper, a generation of models.
