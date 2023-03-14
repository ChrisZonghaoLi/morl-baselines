"""Outer-loop MOQ-learning algorithm (uses multiple weights)."""
import time
from copy import deepcopy
from typing import List, Optional
from typing_extensions import override

import gymnasium as gym
import numpy as np

from morl_baselines.common.evaluation import policy_evaluation_mo
from morl_baselines.common.morl_algorithm import MOAgent
from morl_baselines.common.scalarization import weighted_sum
from morl_baselines.common.utils import (
    equally_spaced_weights,
    log_all_multi_policy_metrics,
    random_weights,
)
from morl_baselines.multi_policy.linear_support.linear_support import LinearSupport
from morl_baselines.single_policy.ser.mo_q_learning import MOQLearning


class MPMOQLearning(MOAgent):
    """Multi-policy MOQ-Learning: Outer loop version of mo_q_learning.

    Paper: Paper: K. Van Moffaert, M. Drugan, and A. Nowe, Scalarized Multi-Objective Reinforcement Learning: Novel Design Techniques. 2013. doi: 10.1109/ADPRL.2013.6615007.
    """

    def __init__(
        self,
        env,
        scalarization=weighted_sum,
        learning_rate: float = 0.1,
        gamma: float = 0.9,
        initial_epsilon: float = 0.1,
        final_epsilon: float = 0.1,
        epsilon_decay_steps: int = None,
        weight_selection_algo: str = "random",
        epsilon_ols: Optional[float] = None,
        use_gpi_policy: bool = False,
        transfer_q_table: bool = True,
        dyna: bool = False,
        dyna_updates: int = 5,
        project_name: str = "MORL-Baselines",
        experiment_name: str = "MultiPolicy MO Q-Learning",
        log: bool = True,
    ):
        """Initialize the Multi-policy MOQ-learning algorithm.

        Args:
            env: The environment to learn from.
            scalarization: The scalarization function to use.
            learning_rate: The learning rate.
            gamma: The discount factor.
            initial_epsilon: The initial epsilon value.
            final_epsilon: The final epsilon value.
            epsilon_decay_steps: The number of steps for epsilon decay.
            weight_selection_algo: The algorithm to use for weight selection. Options: "random", "ols", "gpi-ls"
            epsilon_ols: The epsilon value for the optimistic linear support.
            use_gpi_policy: Whether to use the Generalized Policy Improvement (GPI) or not.
            transfer_q_table: Whether to reuse a Q-table from a previous learned policy when initializing a new policy.
            dyna: Whether to use Dyna-Q or not.
            dyna_updates: The number of Dyna-Q updates to perform.
            project_name: The name of the project for logging.
            experiment_name: The name of the experiment for logging.
            log: Whether to log or not.
        """
        MOAgent.__init__(self, env)
        # Learning
        self.scalarization = scalarization
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.initial_epsilon = initial_epsilon
        self.final_epsilon = final_epsilon
        self.epsilon_decay_steps = epsilon_decay_steps
        self.use_gpi_policy = use_gpi_policy
        self.dyna = dyna
        self.dyna_updates = dyna_updates
        self.transfer_q_table = transfer_q_table
        # Linear support
        self.policies = []
        self.weight_selection_algo = weight_selection_algo
        self.epsilon_ols = epsilon_ols
        assert self.weight_selection_algo in [
            "random",
            "ols",
            "gpi-ls",
        ], f"Unknown weight selection algorithm: {self.weight_selection_algo}."
        self.linear_support = LinearSupport(num_objectives=self.reward_dim, epsilon=epsilon_ols)

        # Logging
        self.project_name = project_name
        self.experiment_name = experiment_name
        self.log = log

        if self.log:
            self.setup_wandb(project_name=self.project_name, experiment_name=self.experiment_name)
        else:
            self.writer = None

    @override
    def get_config(self) -> dict:
        return {
            "env_id": self.env.unwrapped.spec.id,
            "alpha": self.learning_rate,
            "gamma": self.gamma,
            "initial_epsilon": self.initial_epsilon,
            "final_epsilon": self.final_epsilon,
            "epsilon_decay_steps": self.epsilon_decay_steps,
            "scalarization": self.scalarization.__name__,
            "use_gpi_policy": self.use_gpi_policy,
            "weight_selection_algo": self.weight_selection_algo,
            "epsilon_ols": self.epsilon_ols,
            "transfer_q_table": self.transfer_q_table,
            "dyna": self.dyna,
            "dyna_updates": self.dyna_updates,
        }

    def _gpi_action(self, state: np.ndarray, w: np.ndarray) -> int:
        """Get the action given by the GPI policy.

        GPI(s, w) = argmax_a max_pi Q^pi(s, a, w) .

        Args:
            state: The state to get the action for.
            weights: The weights to use for the scalarization.

        Returns:
            The action to take.
        """
        q_vals = np.stack([policy.scalarized_q_values(state, w) for policy in self.policies])
        _, action = np.unravel_index(np.argmax(q_vals), q_vals.shape)
        return int(action)

    def eval(self, obs: np.array, w: Optional[np.ndarray] = None) -> int:
        """If use_gpi is True, return the action given by the GPI policy. Otherwise, chooses the best policy for w and follows it."""
        if self.use_gpi_policy:
            return self._gpi_action(obs, w)
        else:
            best_policy = np.argmax([np.dot(w, v) for v in self.linear_support.ccs])
            return self.policies[best_policy].eval(obs, w)

    def delete_policies(self, delete_indx: List[int]):
        """Delete the policies with the given indices."""
        for i in sorted(delete_indx, reverse=True):
            self.policies.pop(i)

    def train(
        self,
        eval_env: gym.Env,
        ref_point: np.ndarray,
        num_iterations: int,
        timesteps_per_iteration: int,
        known_pareto_front: Optional[List[np.ndarray]] = None,
        eval_weights_number_for_front: int = 100,
        eval_freq: int = 1000,
        num_episodes_eval: int = 10,
    ):
        """Learn a set of policies.

        Args:
            eval_env: The environment to use for evaluation.
            ref_point: The reference point for the hypervolume calculation.
            num_iterations: The number of iterations/policies to train.
            timesteps_per_iteration: The number of timesteps per iteration.
            eval_freq: The frequency of evaluation.
            known_pareto_front: The optimal Pareto front, if known. Used for metrics.
            eval_weights_number_for_front: The number of weights to use to construct a Pareto front for evaluation.
            epsilon_linear_support: The epsilon value for the linear support algorithm.
            num_episodes_eval: The number of episodes used to evaluate the value of a policy.
        """
        if eval_env is None:
            eval_env = deepcopy(self.env)

        eval_weights = equally_spaced_weights(self.reward_dim, n=eval_weights_number_for_front)

        for iter in range(num_iterations):
            if self.weight_selection_algo == "ols" or self.weight_selection_algo == "gpi-ls":
                w = self.linear_support.next_weight(
                    algo=self.weight_selection_algo,
                    gpi_agent=self if self.weight_selection_algo == "gpi-ls" else None,
                    env=eval_env if self.weight_selection_algo == "gpi-ls" else None,
                    rep_eval=num_episodes_eval,
                )
            elif self.weight_selection_algo == "random":
                w = random_weights(self.reward_dim)

            new_agent = MOQLearning(
                env=self.env,
                id=iter,
                weights=w,
                scalarization=self.scalarization,
                learning_rate=self.learning_rate,
                gamma=self.gamma,
                initial_epsilon=self.initial_epsilon,
                final_epsilon=self.final_epsilon,
                epsilon_decay_steps=self.epsilon_decay_steps,
                dyna=self.dyna,
                dyna_updates=self.dyna_updates,
                log=self.log,
                parent_writer=self.writer,
            )
            if self.transfer_q_table and len(self.policies) > 0:
                reuse_ind = np.argmax([np.dot(w, v) for v in self.linear_support.ccs])
                new_agent.q_table = deepcopy(self.policies[reuse_ind].q_table)
            self.policies.append(new_agent)

            start_time = time.time()
            new_agent.global_step = self.global_step
            new_agent.train(
                start_time=start_time,
                total_timesteps=timesteps_per_iteration,
                reset_num_timesteps=False,
                eval_freq=eval_freq,
                eval_env=eval_env,
            )
            self.global_step = new_agent.global_step

            value = policy_evaluation_mo(agent=new_agent, env=eval_env, w=w, rep=num_episodes_eval)[3]
            removed_inds = self.linear_support.add_solution(value, w)
            self.delete_policies(removed_inds)

            if self.log:
                if self.use_gpi_policy:
                    front = [
                        policy_evaluation_mo(agent=self, env=eval_env, w=w, rep=num_episodes_eval)[3] for w in eval_weights
                    ]
                else:
                    front = self.linear_support.ccs
                log_all_multi_policy_metrics(
                    current_front=front,
                    hv_ref_point=ref_point,
                    reward_dim=self.reward_dim,
                    global_step=self.global_step,
                    writer=self.writer,
                    ref_front=known_pareto_front,
                )

        if self.writer is not None:
            self.close_wandb()
