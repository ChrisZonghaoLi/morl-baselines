<img src="docs/_static/_images/mo_cheetah.gif" alt="Multiple policies" align="right" width="50%"/>


[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
![tests](https://github.com/LucasAlegre/morl-baselines/workflows/Python%20tests/badge.svg)
[![License](http://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](https://github.com/LucasAlegre/morl-baselines/blob/main/LICENSE)
[![Discord](https://img.shields.io/discord/999693014618362036?label=discord)](https://discord.gg/ygmkfnBvKA)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

# MORL-Baselines

<!-- start elevator-pitch -->

MORL-Baselines is a library of Multi-Objective Reinforcement Learning (MORL) algorithms.
This repository aims at containing reliable MORL algorithms implementations in PyTorch.

It strictly follows [MO-Gymnasium](https://github.com/Farama-Foundation/mo-gymnasium) API, which differs from the standard [Gymnasium](https://github.com/Farama-Foundation/Gymnasium) API only in that the environment returns a numpy array as the reward.

For details on multi-objective MDP's (MOMDP's) and other MORL definitions, we suggest reading [A practical guide to multi-objective reinforcement learning and planning](https://link.springer.com/article/10.1007/s10458-022-09552-y).

<!-- end elevator-pitch -->

## Features

<!-- start features -->

* Single and multi-policy algorithms under both SER and ESR criteria are implemented.
* All algorithms follow the [MO-Gymnasium](https://www.github.com/Farama-Foundation/mo-gymnasium) API.
* Performances are automatically reported in [Weights and Biases](https://wandb.ai/) dashboards.
* Linting and formatting are enforced by pre-commit hooks.
* Code is well documented.
* All algorithms are automatically tested.
* Utility functions are provided e.g. pareto pruning, experience buffers, etc.
* 🔜 Performances have been tested against the ones reported in the original papers.
* 🔜 Hyper-parameter optimization available.

<!-- end features -->


## Implemented Algorithms

<!-- start algos-list -->

| **Name**                                                                                                                                                                 | Single/Multi-policy | ESR/SER | Observation space | Action space | Paper                                                                                                                       |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------|---------|------------------|--------------|-----------------------------------------------------------------------------------------------------------------------------|
| [GPI-LS + GPI-PD](https://github.com/LucasAlegre/morl-baselines/blob/main/morl_baselines/multi_policy/gpi_pd/gpi_pd.py)                                      | Multi               | SER     | Continuous       | Discrete / Continuous     | [Paper and Supplementary Materials](https://arxiv.org/abs/2301.07784)
| [Envelope Q-Learning](https://github.com/LucasAlegre/morl-baselines/blob/main/morl_baselines/multi_policy/envelope/envelope.py)                                      | Multi               | SER     | Continuous       | Discrete     | [Paper](https://arxiv.org/pdf/1908.08342.pdf)                                                                                        |
| [PGMORL](https://github.com/LucasAlegre/morl-baselines/blob/main/morl_baselines/multi_policy/pgmorl/pgmorl.py) <sup>[1](#f1)</sup>                                                     | Multi               | SER     | Continuous       | Continuous   | [Paper](https://people.csail.mit.edu/jiex/papers/PGMORL/paper.pdf) / [Supplementary Materials](https://people.csail.mit.edu/jiex/papers/PGMORL/supp.pdf)        |
| [Pareto Conditioned Networks (PCN)](https://github.com/LucasAlegre/morl-baselines/blob/main/morl_baselines/multi_policy/pcn/pcn.py)                                      | Multi               | SER/ESR <sup>[2](#f2)</sup>      | Continuous       | Discrete     | [Paper](https://www.ifaamas.org/Proceedings/aamas2022/pdfs/p1110.pdf)                                                          |
| [Pareto Q-Learning](https://github.com/LucasAlegre/morl-baselines/blob/main/morl_baselines/multi_policy/pareto_q_learning/pql.py)                                    | Multi               | SER     | Discrete         | Discrete     | [Paper](https://jmlr.org/papers/volume15/vanmoffaert14a/vanmoffaert14a.pdf)                                                          |
| [MO Q learning](https://github.com/LucasAlegre/morl-baselines/blob/main/morl_baselines/single_policy/ser/mo_q_learning.py)                                           | Single              | SER     | Discrete         | Discrete     | [Paper](https://www.researchgate.net/publication/235698665_Scalarized_Multi-Objective_Reinforcement_Learning_Novel_Design_Techniques)                                                                                                                             |
| [MPMOQLearning](https://github.com/LucasAlegre/morl-baselines/blob/main/morl_baselines/multi_policy/multi_policy_moqlearning/mp_mo_q_learning.py)  (outer loop MOQL) | Multi               | SER     | Discrete         | Discrete     | [Paper](https://www.researchgate.net/publication/235698665_Scalarized_Multi-Objective_Reinforcement_Learning_Novel_Design_Techniques) |
| [Optimistic Linear Support (OLS)](https://github.com/LucasAlegre/morl-baselines/blob/main/morl_baselines/multi_policy/ols/ols.py)                                    | Multi               | SER     | /                | /            | Section 3.3 of the [thesis](http://roijers.info/pub/thesis.pdf)     |
| [Expected Utility Policy Gradient (EUPG)](https://github.com/LucasAlegre/morl-baselines/blob/main/morl_baselines/single_policy/esr/eupg.py)                          | Single              | ESR     | Discrete         | Discrete     |   [Paper](https://www.researchgate.net/publication/328718263_Multi-objective_Reinforcement_Learning_for_the_Expected_Utility_of_the_Return)                                                   |

:warning: The algorithms have not been benchmarked yet, and some of them have limited features.

<b id="f1">1</b>: Currently, PGMORL is limited to environments with 2 objectives.

<b id="f2">2</b>: PCN assumes environments with deterministic transitions.

<!-- end algos-list -->

## Structure

<!-- start structure -->
As much as possible, this repo tries to follow the single-file implementation rule for all algorithms. The repo's structure is as follows:

* `examples/` contains a set of examples to use MORL Baselines with [MO-Gymnasium](https://www.github.com/Farama-Foundation/mo-gymnasium) environments.
* `common/` contains the implementation recurring concepts: replay buffers, neural nets, etc. See the [documentation](https://lucasalegre.github.io/morl-baselines/) for more details.
* `multi_policy/` contains the implementations of multi-policy algorithms.
* `single_policy/` contains the implementations of single-policy algorithms (ESR and SER).

<!-- end structure -->


## Citing the Project

<!-- start citing -->

```bibtex
@misc{morl_baselines,
    author = {Florian Felten and Lucas N. Alegre},
    title = {MORL-Baselines: Multi-Objective Reinforcement Learning algorithms implementations},
    year = {2022},
    publisher = {GitHub},
    journal = {GitHub repository},
    howpublished = {\url{https://github.com/LucasAlegre/morl-baselines}},
}
```

<!-- end citing -->

## Maintainers

<!-- start maintainers -->
MORL-Baselines is currently maintained by [Florian Felten](https://ffelten.github.io/) (@ffelten) and [Lucas N. Alegre](https://www.inf.ufrgs.br/~lnalegre/) (@LucasAlegre).
<!-- end maintainers -->

## Contributing

<!-- start contributing -->
This repository is open to contributions and we are always happy to receive new algorithms, bug fixes, or features. If you want to contribute, you can join our [Discord server](https://discord.gg/ygmkfnBvKA) and discuss your ideas with us. You can also open an issue or a pull request directly.

<!-- end contributing -->

## Acknowledgements
<!-- start acknowledgements -->
* Willem Röpke, for his implementation of Pareto Q-Learning (@wilrop)
* Denis Steckelmacher and Conor F. Hayes, for providing us with the original implementation of EUPG.
<!-- end acknowledgements -->
