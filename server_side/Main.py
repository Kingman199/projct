from Database.DatabaseParent import DatabaseParent
from Network import Network
from installer import main

if __name__ == '__main__':
    main()
    Network( DatabaseParent() )
