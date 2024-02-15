# AIO

### Issues:
- Installing IO::Socket::INET6 failed
    * Install libio-socket-inet6-perl from apt
- Configure failed for Net-SSLeay-1.94
    * Install zlib1g-dev libssl-dev from apt
- Install Perl module Package::Stash::XS, Readonly, HTTP::Request
- Installing Unicode::String, Term::ReadKey, Sys::MemInfo failed
    * Install libunicode-string-perl, libterm-readkey-perl, libsys-meminfo-perl from apt


# Celery


# Django

### Issues:
- cpan PAR::Packer failed.
    * install libpar-packer-perl from apt
- cpan Test::Mock::Guard failed
    * install libtest-mock-guard-perl from apt
- cpan JSON::WebToken issues
    * install libjson-webtoken-perl from apt
- LWP::UserAgent issues
    * install libwww-perl from apt
### Notes:

- Python docker images require the following perl modules to run imapsync (since the image is based on debian everything should be available):
    Authen::NTLM , CGI , Crypt::OpenSSL::RSA , Data::Uniqid , Digest::HMAC , Digest::HMAC_MD5 , Dist::CheckConflicts , Encode::IMAPUTF7 , File::Copy::Recursive , File::Tail , IO::Socket::INET6 , IO::Socket::SSL , IO::Tee , JSON , JSON::WebToken , JSON::WebToken::Crypt::RSA , LWP::UserAgent , Module::ScanDeps , Net::SSLeay , PAR::Packer , Proc::ProcessTable , Regexp::Common , Sys::MemInfo , Term::ReadKey , Test::Fatal , Test::Mock::Guard , Test::MockObject , Test::Pod , Test::Requires , Test::Deep , Unicode::String

