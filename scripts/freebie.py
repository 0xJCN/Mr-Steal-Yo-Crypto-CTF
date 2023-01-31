from ape import accounts, project
from .utils.helper import w3, MAX_UINT256

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

    # deploy FARM token contract
    print("\n--- Deploying FARM Token ---\n")
    farm = project.Token.deploy("FARM", "FARM", sender=admin)
    farm.mintPerUser(
        [admin_user.address, attacker.address],
        [INITIAL_STAKING_TOKEN_BALANCE, INITIAL_ATTACKER_TOKEN_BALANCE],
        sender=admin,
    )
    # deploy protocol contracts
    print("\n--- Deploying Protocol Contracts ---\n")
    gov_token = project.GovToken.deploy("xFARM", "xFARM", sender=admin)

    rewards_advisor = project.RewardsAdvisor.deploy(
        farm.address,
        gov_token.address,
        sender=admin,
    )
    gov_token.transferOwnership(rewards_advisor, sender=admin)

    # other user stakes their "FARM" token
    print("\n--- Admin User is staking their Farm token ---\n")
    farm.approve(rewards_advisor.address, MAX_UINT256, sender=admin_user)
    rewards_advisor.deposit(
        INITIAL_STAKING_TOKEN_BALANCE,
        admin_user.address,
        admin_user.address,
        sender=admin_user,
    )

    # define initial balances for staking contract and attacker
    advisor_initial_bal = farm.balanceOf(rewards_advisor.address) / 10**18
    attacker_initial_bal = farm.balanceOf(attacker.address) / 10**18

    print(
        f"\n--- \nInitial Balances:\n⇒ Rewards Advisor: {advisor_initial_bal}\n⇒ Attacker: {attacker_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- After expoit: attacker drains 99.99%+ of the `FARM` tokens from RewardsAdvisor staking contract ---\n"
    )

    # define initial balances for staking contract and attacker
    advisor_ending_bal = farm.balanceOf(rewards_advisor.address) / 10**18
    attacker_ending_bal = farm.balanceOf(attacker.address) / 10**18

    print(
        f"\n--- \nEnding Balances:\n⇒ Rewards Advisor: {advisor_ending_bal}\n⇒ Attacker: {attacker_ending_bal}\n---\n"
    )
    assert farm.balanceOf(attacker.address) > INITIAL_STAKING_TOKEN_BALANCE
    assert farm.balanceOf(rewards_advisor.address) < INITIAL_ATTACKER_TOKEN_BALANCE

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
