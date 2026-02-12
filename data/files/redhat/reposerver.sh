[base]
name=Base
baseurl=http://>>reposerver<</repo/>>dist<</>>major<</>>arch<</base
enabled=1
protect=1
gpgcheck=1
gpgkey=http://>>reposerver<</repo/>>dist<</>>major<</>>arch<</RPM-GPG-KEY->>dist<<->>major<<

[updates]
name=Updates
baseurl=http://>>reposerver<</repo/>>dist<</>>major<</>>arch<</updates
enabled=1
protect=1
gpgcheck=1
gpgkey=http://>>reposerver<</repo/>>dist<</>>major<</>>arch<</RPM-GPG-KEY->>dist<<->>major<<

[optional]
name=Optional packages
baseurl=http://>>reposerver<</repo/>>dist<</>>major<</>>arch<</optional
enabled=0
protect=1
gpgcheck=1
gpgkey=http://>>reposerver<</repo/>>dist<</>>major<</>>arch<</RPM-GPG-KEY->>dist<<->>major<<

[extras]
name=Extra packages
baseurl=http://>>reposerver<</repo/>>dist<</>>major<</>>arch<</extras
enabled=0
protect=1
gpgcheck=1
gpgkey=http://>>reposerver<</repo/>>dist<</>>major<</>>arch<</RPM-GPG-KEY->>dist<<->>major<<

[ha]
name=High Availability packages
baseurl=http://>>reposerver<</repo/>>dist<</>>major<</>>arch<</ha
enabled=0
protect=1
gpgcheck=1
gpgkey=http://>>reposerver<</repo/>>dist<</>>major<</>>arch<</RPM-GPG-KEY->>dist<<->>major<<
