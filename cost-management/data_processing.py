import pandas as pd 
import numpy as np

def data_processing():
    aws_report = pd.read_csv('cost-and-usage-report-aws.csv', delimiter=',', low_memory=False)
    gcp_report = pd.read_csv('cost-and-usage-report-gcp.csv', delimiter=',', low_memory=False)

    # Convert the columns to numeric values, forcing any non-numeric values to NaN for AWS
    numeric_columns = aws_report.select_dtypes(include=[np.number]).columns
    aws_report[numeric_columns] = aws_report[numeric_columns].fillna(0.0)

    # Drop columns that are not needed
    gcp_report.drop(['Subtotal (€)', 'Unrounded subtotal (€)'], axis=1, inplace=True)  
    aws_report.drop(['bill_bill_type', 'bill_billing_entity', 'bill_invoice_id', 'bill_invoicing_entity', 
                    'bill_payer_account_id', 'bill_payer_account_name', 'bill_billing_period_end_date', 
                    'bill_billing_period_start_date', 'cost_category', 'discount', 'identity_line_item_id', 
                    'line_item_availability_zone', 'line_item_currency_code', 
                    'line_item_line_item_type', 'line_item_net_unblended_cost', 'line_item_net_unblended_rate', 
                    'line_item_normalization_factor', 'split_line_item_net_split_cost', 'split_line_item_net_unused_cost', 
                    'split_line_item_parent_resource_id', 'split_line_item_public_on_demand_split_cost', 
                    'split_line_item_public_on_demand_unused_cost', 'split_line_item_reserved_usage', 
                    'split_line_item_split_cost', 'split_line_item_split_usage', 
                    'split_line_item_split_usage_ratio', 'split_line_item_unused_cost', 
                    'line_item_normalized_usage_amount', 'savings_plan_purchase_term', 
                    'savings_plan_recurring_commitment_for_billing_period', 'line_item_tax_type', 
                    'savings_plan_offering_type', 'savings_plan_payment_option', 'savings_plan_region', 
                    'savings_plan_savings_plan_a_r_n', 'savings_plan_savings_plan_effective_cost', 
                    'split_line_item_actual_usage', 'savings_plan_used_commitment', 
                    'savings_plan_total_commitment_to_date', 'savings_plan_start_time', 'savings_plan_savings_plan_rate', 
                    'savings_plan_net_savings_plan_effective_cost', 'reservation_unused_normalized_unit_quantity', 
                    'reservation_unused_quantity', 'reservation_unused_recurring_fee', 'reservation_upfront_value', 
                    'resource_tags', 'savings_plan_amortized_upfront_commitment_for_billing_period', 'savings_plan_end_time', 
                    'savings_plan_instance_type_family', 'savings_plan_net_amortized_upfront_commitment_for_billing_period', 
                    'savings_plan_net_recurring_commitment_for_billing_period', 'reservation_normalized_units_per_reservation', 
                    'reservation_number_of_reservations', 'reservation_recurring_fee_for_usage', 
                    'reservation_reservation_a_r_n', 'reservation_start_time', 'reservation_subscription_id', 
                    'reservation_net_amortized_upfront_fee_for_billing_period', 'reservation_net_effective_cost', 
                    'reservation_net_recurring_fee_for_usage', 'reservation_net_unused_amortized_upfront_fee_for_billing_period', 
                    'reservation_unused_amortized_upfront_fee_for_billing_period', 
                    'reservation_units_per_reservation', 'reservation_total_reserved_units', 'reservation_total_reserved_normalized_units', 
                    'reservation_net_upfront_value', 'reservation_net_unused_recurring_fee', 'reservation_net_amortized_upfront_cost_for_usage', 
                    'reservation_modification_status', 'reservation_end_time', 'reservation_effective_cost', 'reservation_availability_zone', 
                    'reservation_amortized_upfront_fee_for_billing_period', 'reservation_amortized_upfront_cost_for_usage', 
                    'product_sku', 'product_to_location_type', 'product_product_family', 'product_pricing_unit', 
                    'product_operation', 'product_location_type', 'product_instancesku', 'product_instance_type', 
                    'product_instance_family', 'product_from_region_code', 'product_from_location_type', 
                    'product_from_location', 'product_fee_code', 'product_fee_description', 'product_comment', 
                    'product', 'pricing_unit', 'pricing_term', 'pricing_rate_id', 'pricing_rate_code', 'pricing_purchase_option', 
                    'pricing_public_on_demand_cost', 'pricing_public_on_demand_rate', 'pricing_offering_class', 'pricing_lease_contract_length', 
                    'pricing_currency', 'line_item_usage_type', 'line_item_usage_start_date', 'line_item_usage_end_date', 
                    'line_item_usage_account_name', 'line_item_unblended_rate'], axis=1, inplace=True)   
    
    # Make a proper datetime format
    aws_report['date'] = aws_report['identity_time_interval'].apply(lambda x: x.split('T')[0])

    # Group the data by date, product code, and region code
    grouped_data = aws_report.groupby(['date', 'line_item_product_code', 'product_region_code']).first().reset_index() 
    grouped_data.drop('identity_time_interval', axis=1, inplace=True) 

    # Calculate the cost after applying discounts and promotions
    cost = grouped_data['line_item_blended_cost'] - (grouped_data['discount_bundled_discount'] + grouped_data['discount_total_discount'])
    grouped_data['cost'] = cost

    # Drop the columns that are not needed
    grouped_data.drop('line_item_blended_cost', axis=1, inplace=True)
    grouped_data.drop('discount_bundled_discount', axis=1, inplace=True)
    grouped_data.drop('discount_total_discount', axis=1, inplace=True)

    # Convert the columns to numeric values, forcing any non-numeric values to NaN for GCP
    gcp_report['Cost (€)'] = pd.to_numeric(gcp_report['Cost (€)'], errors='coerce')
    gcp_report['Discounts (€)'] = pd.to_numeric(gcp_report['Discounts (€)'], errors='coerce') 
    gcp_report['Promotions and others (€)'] = pd.to_numeric(gcp_report['Promotions and others (€)'], errors='coerce')

    # Calculate the cost after applying discounts and promotions
    cost = gcp_report['Cost (€)'] - (gcp_report['Discounts (€)'] + gcp_report['Promotions and others (€)'])
    # Add the result to the DataFrame
    gcp_report['Cost'] = cost
    
    # Drop the old cost columns
    gcp_report.drop('Cost (€)', axis=1, inplace=True)
    gcp_report.drop('Discounts (€)', axis=1, inplace=True)
    gcp_report.drop('Promotions and others (€)', axis=1, inplace=True)
    grouped_data = grouped_data[grouped_data['cost'] != 0]

    # Drop duplicates
    gcp_report.drop_duplicates(inplace=True) 
    aws_report.drop_duplicates(inplace=True)

    # Save the cleaned data to a new CSV file and sort the data by date
    df_aws = grouped_data.sort_values(by='date')
    df_gcp = gcp_report.sort_values(by='Date')
    df_aws.to_csv('clean-cost-and-usage-report-aws.csv', index=False)
    df_gcp.to_csv('clean-cost-and-usage-report-gcp.csv', index=False)