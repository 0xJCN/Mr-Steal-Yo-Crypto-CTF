from ape import accounts, project
from .utils.helper import get_block


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    attacker = accounts.test_accounts[1]
    user_1 = accounts.test_accounts[2]
    user_2 = accounts.test_accounts[3]
    admin = accounts.test_accounts[0]

    print(
        f"\n--- \nOur players:\n⇒ Admin: {admin}\n⇒ Attacker: {attacker}\n⇒ User 1: {user_1}\n⇒ User 2: {user_2}\n---\n"
    )

    # deploy token and pool contracts
    print("\n--- Deploying NFT Marketplace contract ---\n")
    nft_market = project.FlatLaunchpeg.deploy(69, 5, 5, sender=admin)

    start_block = get_block()

    # define initial balance for attacker
    attacker_initial_bal = nft_market.balanceOf(attacker.address)

    print(f"\n--- \nInitial Balances:\n⇒ Attacker: {attacker_initial_bal}\n---\n")

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print("\n--- After exploit: Attacker is in possession of entire collection ---\n")

    # define ending balances for attacker and wallet
    attacker_ending_bal = nft_market.balanceOf(attacker.address)

    print(f"\n--- \nEnding Balances:\n⇒ Attacker: {attacker_ending_bal}\n---\n")

    assert nft_market.totalSupply() == 69
    assert nft_market.balanceOf(attacker.address) == 69
    assert get_block() == start_block + 1

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
