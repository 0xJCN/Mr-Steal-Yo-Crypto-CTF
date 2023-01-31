from ape import accounts, project
from .utils.helper import w3, time_travel, MAX_UINT256

INITIAL_STAKING_TOKEN_BALANCE = w3.to_wei(100000, "ether")
INITIAL_ATTACKER_TOKEN_BALANCE = w3.to_wei(1, "ether")


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    admin = accounts.test_accounts[0]
    admin_user = accounts.test_accounts[1]
    attacker = accounts.test_accounts[2]

    print(
        f"\n--- \nOur players:\n⇒ Admin: {admin}\n⇒ Admin User: {admin_user}\n⇒ Attacker: {attacker}\n---\n"
    )

    # deploy steak token
    print("\n--- Deploying Steak Token ---\n")
    steak = project.Token.deploy("STEAK", "STEAK", sender=admin)
    steak.mintPerUser(
        [admin_user.address, attacker.address],
        [INITIAL_STAKING_TOKEN_BALANCE, INITIAL_ATTACKER_TOKEN_BALANCE],
        sender=admin,
    )

    # deploy butter token
    print("\n--- Deploying Butter Token ---\n")
    butter = project.Token.deploy("BUTTER", "BUTTER", sender=admin)
    butter.mintPerUser(
        [admin.address],
        [INITIAL_STAKING_TOKEN_BALANCE],
        sender=admin,
    )

    # deploy tasty staking contract
    print("\n--- Deploying Staking Contract ---\n")
    tasty_staking = project.TastyStaking.deploy(
        steak.address,
        admin.address,
        sender=admin,
    )
    # setting up rewards for tasty staking
    print("\n--- Setting up rewards for staking contract ---\n")
    tasty_staking.addReward(butter.address, sender=admin)
    butter.approve(
        tasty_staking.address,
        INITIAL_STAKING_TOKEN_BALANCE,
        sender=admin,
    )
    tasty_staking.notifyRewardAmount(
        butter.address,
        INITIAL_STAKING_TOKEN_BALANCE,
        sender=admin,
    )
    # other user stakes initial amount of steak
    print("\n--- Admin User is staking their initial steak tokens ---\n")
    steak.approve(tasty_staking.address, MAX_UINT256, sender=admin_user)
    tasty_staking.stakeAll(sender=admin_user)
    assert steak.balanceOf(tasty_staking) == INITIAL_STAKING_TOKEN_BALANCE

    # advance time by an hour
    print("\n--- 1 hour later ... ---\n")
    time_travel(3600)

    # define initial balances for staking contract and attacker
    staking_initial_bal = steak.balanceOf(tasty_staking.address) / 10**18
    attacker_initial_bal = steak.balanceOf(attacker.address) / 10**18

    print(
        f"\n--- \nInitial Balances:\n⇒ Staking Contract: {staking_initial_bal}\n⇒ Attacker: {attacker_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- After expoit: attacker drains all staking tokens from tastyStaking contract ---\n"
    )

    # define initial balances for staking contract and attacker
    staking_ending_bal = steak.balanceOf(tasty_staking.address) / 10**18
    attacker_ending_bal = steak.balanceOf(attacker.address) / 10**18

    print(
        f"\n--- \nEnding Balances:\n⇒ Staking Contract: {staking_ending_bal}\n⇒ Attacker: {attacker_ending_bal}\n---\n"
    )

    assert steak.balanceOf(tasty_staking.address) == 0
    assert steak.balanceOf(attacker.address) > INITIAL_STAKING_TOKEN_BALANCE

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
