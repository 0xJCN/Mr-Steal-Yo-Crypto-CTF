from ape import accounts, project
from .utils.helper import w3


def main():
    # --- BEFORE EXPLOIT --- #
    print("\n--- Setting up scenario ---\n")

    # get accounts
    attacker = accounts.test_accounts[0]
    admin = accounts.test_accounts[1]
    admin_user = accounts.test_accounts[2]

    print(
        f"\n--- \nOur players:\n⇒ Admin: {admin}\n⇒ Admin User: {admin_user}\n⇒ Attacker: {attacker}\n---\n"
    )

    # deploy asset wrapper
    print("\n--- Deploying asset wrapper ---\n")
    wrapper = project.AssetWrapper.deploy("", sender=admin)

    # deploy sword asset
    print("\n--- Deploying Sword asset ---\n")
    sword = project.GameAsset.deploy("SWORD", "SWORD", sender=admin)

    # deploy shield asset
    print("\n--- Deploying Shield asset ---\n")
    shield = project.GameAsset.deploy("SHIELD", "SHIELD", sender=admin)

    # whitelist the two assets for use in the game
    print("\n--- Whitelisting both game assets ---\n")
    wrapper.updateWhitelist(sword.address, sender=admin)
    wrapper.updateWhitelist(shield.address, sender=admin)

    assert wrapper.isWhitelisted(sword.address)
    assert wrapper.isWhitelisted(shield.address)

    # set the operator of the two game assets to be the wrapper contract
    print("\n--- Setting the operator for both game assets ---\n")
    sword.setOperator(wrapper.address, sender=admin)
    shield.setOperator(wrapper.address, sender=admin)

    assert (
        w3.toChecksumAddress("0x" + w3.eth.get_storage_at(sword.address, 2).hex()[26:])
        == wrapper.address
    )
    assert (
        w3.toChecksumAddress("0x" + w3.eth.get_storage_at(shield.address, 2).hex()[26:])
        == wrapper.address
    )

    # adminUser is the user you will be griefing
    # minting 1 SWORD & 1 SHIELD asset for adminUser
    print("\n--- Minting game asserts for Admin User ---\n")
    sword.mintForUser(admin_user.address, 1, sender=admin)
    shield.mintForUser(admin_user.address, 1, sender=admin)

    assert sword.balanceOf(admin_user.address) == 1
    assert shield.balanceOf(admin_user.address) == 1

    # define initial balances for admin user and wrapper contract
    admin_user_initial_bal = sword.balanceOf(admin_user.address) + shield.balanceOf(
        admin_user.address
    )
    wrapper_initial_bal = sword.balanceOf(wrapper.address) + shield.balanceOf(
        wrapper.address
    )

    print(
        f"\n--- \nInitial Balances:\n⇒ Admin User: {admin_user_initial_bal}\n⇒ Wrapper: {wrapper_initial_bal}\n---\n"
    )

    # --- EXPLOIT GOES HERE --- #
    print("\n--- Initiating exploit... ---\n")

    # exploit

    # --- AFTER EXPLOIT --- #
    print(
        "\n--- After exploit: Attacker griefed Admin User and locked their NFTs in wrapper contract ---\n"
    )

    # define ending balances for admin user and wrapper contract
    admin_user_ending_bal = sword.balanceOf(admin_user.address) + shield.balanceOf(
        admin_user.address
    )
    wrapper_ending_bal = sword.balanceOf(wrapper.address) + shield.balanceOf(
        wrapper.address
    )

    print(
        f"\n--- \nEnding Balances:\n⇒ Admin User: {admin_user_ending_bal}\n⇒ Wrapper: {wrapper_ending_bal}\n---\n"
    )

    # attacker traps user's SWORD and SHIELD NFTs inside assetWrapper contract
    assert sword.balanceOf(admin_user.address) == 0
    assert shield.balanceOf(admin_user.address) == 0

    assert sword.balanceOf(wrapper.address) == 1
    assert shield.balanceOf(wrapper.address) == 1

    assert wrapper.balanceOf(admin_user.address, 0) == 0
    assert wrapper.balanceOf(admin_user.address, 1) == 0

    print("\n--- 🥂 Challenge Completed! 🥂---\n")


if __name__ == "__main__":
    main()
