

%redirect_params = (
	job_type => 'email',
	microsoft_tenant_id => 'b77',
);
if (1) {
	$redirect_params{migrate_task_id} = "jfdlksjfdk";
}

use Data::Dumper;
print Dumper(\%redirect_params);
