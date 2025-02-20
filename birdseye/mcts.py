import argparse
import configparser
from datetime import datetime
from types import SimpleNamespace

from .actions import SimpleActions
from .env import RFEnv
from .mcts_utils import mcts_trial
from .sensor import Drone
from .state import RFState
from .utils import Results
from .utils import write_header_log


def run_mcts(
    env, config=None, fig=None, ax=None, global_start_time=None, mcts_defaults={}
):
    """Function to run Monte Carlo Tree Search

    Parameters
    ----------
    env : object
        Environment definitions
    config : object
        Config object which must have following:

    simulations : int
        Number of simulations
    DEPTH : int
        Tree depth
    lambda_arg : float
        Lambda value
    num_runs : int
        Number of runs
    iterations : int
        Number of iterations
    COLLISION_REWARD : float
        Reward value for collision
    LOSS_REWARD : float
        Reward value for loss function
    plotting : bool
        Flag to plot or not
    ------------
    fig : object
        Figure object
    ax : object
        Axis object
    """
    if config is None:
        config = SimpleNamespace(**mcts_defaults)
    simulations = config.simulations
    DEPTH = config.depth
    num_runs = config.trials
    iterations = config.iterations
    plotting = config.plotting

    # Results instance for saving results to file
    results = Results(
        method_name="mcts",
        global_start_time=global_start_time,
        num_iters=num_runs,
        plotting=plotting,
    )

    run_data = []

    # trials
    mcts_loss = 0
    mcts_coll = 0
    for i in range(1, num_runs + 1):
        run_start_time = datetime.now()
        result = mcts_trial(
            env,
            iterations,
            DEPTH,
            20,
            plotting,
            simulations,
            fig=fig,
            ax=ax,
            results=results,
        )
        run_time = datetime.now() - run_start_time
        run_data.append([datetime.now(), run_time] + result[1:])

        # mcts_coll = result[6][-1]/iterations
        # mcts_loss = result[7][-1]/iterations
        mcts_coll = result[6][-1]
        mcts_loss = result[7][-1]
        print(".")
        print("\n==============================")
        print(f"Runs: {i}")
        print(f"SIMULATIONS: {simulations}")
        print(f"MCTS Depth {DEPTH} Results")
        print(f"Collision Rate: {mcts_coll/i}")
        print(f"Loss Rate: {mcts_loss/i}")
        print("==============================")

        # Saving results to CSV file
        results.write_dataframe(run_data=run_data)
        if results.plotting:
            results.save_gif(i)


def mcts(args=None, env=None, mcts_defaults={}):
    # Grab mcts specific defaults
    defaults = mcts_defaults
    config = None

    if args:
        config = configparser.ConfigParser(defaults)  # pytype: disable=wrong-arg-types
        config.read_dict({section: dict(args[section]) for section in args.sections()})
        defaults = dict(config.items("Defaults"))
        # Fix for boolean args
        defaults["plotting"] = config.getboolean("Defaults", "plotting")

    parser = argparse.ArgumentParser(
        description="Monte Carlo Tree Search",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.set_defaults(**defaults)
    parser.add_argument("--lambda_arg", type=float, help="Lambda value")
    parser.add_argument("--collision", type=float, help="Reward value for collision")
    parser.add_argument("--loss", type=float, help="Reward value for loss function")
    parser.add_argument("--depth", type=float, help="Tree depth")
    parser.add_argument("--simulations", type=int, help="Number of simulations")
    parser.add_argument("--plotting", type=bool, help="Flag to plot or not")
    parser.add_argument("--trials", type=int, help="Number of runs")
    parser.add_argument("--iterations", type=int, help="Number of iterations")
    args, _ = parser.parse_known_args()

    if not env:
        # Setup environment
        actions = SimpleActions()
        sensor = Drone()
        state = RFState()
        env = RFEnv(sensor, actions, state)

    global_start_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if config:
        write_header_log(config, "mcts", global_start_time)

    run_mcts(
        env=env,
        config=args,
        global_start_time=global_start_time,
        mcts_defaults=mcts_defaults,
    )


if __name__ == "__main__":  # pragma: no cover
    # Default MCTS inputs
    mcts_defaults = {
        "lambda_arg": 0.8,
        "collision": -2.0,
        "loss": -2.0,
        "depth": 10,
        "simulations": 500,
        "plotting": False,
        "trials": 100,
        "iterations": 500,
    }

    mcts(mcts_defaults=mcts_defaults)
