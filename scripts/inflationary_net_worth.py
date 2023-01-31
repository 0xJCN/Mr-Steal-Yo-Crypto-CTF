from ape import accounts, project
from .utils.helper import w3, get_block, MAX_UINT256

INITIAL_TOKEN_BALANCE = w3.to_wei(10000, "ether")


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

    # deploy MULA token
    print("\n--- Deploying MULA & MUNY Token ---\n")
    mula = project.MulaToken.deploy("MULA", "MULA", sender=admin)
    mula.mintPerUser(
        [admin_user.address, attacker.address],
        [INITIAL_TOKEN_BALANCE, INITIAL_TOKEN_BALANCE],
        sender=admin,
    )
    muny = project.Token.deploy("MUNY", "MUNY", sender=admin)

    # deploy Master Chef Contract
    print("\n--- Deploying Master Chef Contract ---\n")
    master_chef = project.MasterChef.deploy(
        muny.address,
        admin.address,
        w3.to_wei(1, "ether"),
        get_block(),
        get_block(),
        sender=admin,
    )
    muny.transferOwnership(master_chef.address, sender=admin)

    # starting MULA staking
    print("\n--- Admin User is staking MULA token in Master Chef ---\n")
    master_chef.add(1000, mula.address, False, sender=admin)  # init staking

    mula.approve(master_chef.address, MAX_UINT256, sender=admin_user)
    master_chef.deposit(0, INITIAL_TOKEN_BALANCE, sender=admin_user)

    start_block = get_block()  # first reward block

    # define initial balances for master chef, admin user, attacker
    chef_initial_bal = muny.balanceOf(master_chef.address) / 10**18
    user_initial_bal = muny.balanceOf(admin_user.address) / 10**18
    attacker_initial_bal = muny.balanceOf(attacker.address) / 10**18
    print(
        f"\n--- \nInitial Balances:\n⇒ Master Chef: {chef_initial_bal}\n⇒ Admin User: {user_initial_bal}"
    )
    print(f"⇒ Attacker: {attacker_initial_bal}\n---\n")

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- After expoit: attacker drains all farm emissions up to this block ---\n"
    )

    # define ending balances for master chef, admin user, and attacker
    chef_ending_bal = muny.balanceOf(master_chef.address) / 10**18
    user_ending_bal = muny.balanceOf(admin_user.address) / 10**18
    attacker_ending_bal = muny.balanceOf(attacker.address) / 10**18

    print(
        f"\n--- \nEnding Balances:\n⇒ Master Chef: {chef_ending_bal}\n⇒ Admin User: {user_ending_bal}"
    )
    print(f"⇒ Attacker: {attacker_ending_bal}\n---\n")

    end_block = get_block()
    assert muny.balanceOf(attacker.address) > 0
    assert muny.balanceOf(attacker.address) == (10**18) * (
        end_block - start_block
    )  # all rewards issued from startBlock - endBlock
    muny.balanceOf(master_chef.address) == 0
    muny.balanceOf(admin_user.address) == 0

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
